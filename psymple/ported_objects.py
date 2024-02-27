from abc import ABC, abstractmethod
from typing import List

import sympy as sym

from copy import deepcopy
from psymple.abstract import DependencyError, SymbolWrapper
from psymple.variables import (
    Parameter,
    Parameters,
    # SimParameter,
    SimUpdateRule,
    SimVariable,
    Variable,
    Variables,
    UpdateRule,
)

HIERARCHY_SEPARATOR = '.'

class WiringError(Exception):
    pass

class Assignment:
    def __init__(self, symbol_wrapper, expression):
        if type(symbol_wrapper) is str:
            symbol_wrapper = SymbolWrapper(sym.Symbol(symbol_wrapper))
        self.symbol_wrapper = symbol_wrapper
        if type(expression) is str:
            expression = sym.sympify(expression)
        self.expression = expression

    def get_free_symbols(self, global_symbols={}):
        assignment_symbols = sym.sympify(assignment.expression).free_symbols
        return assignment_symbols - global_symbols - {self.symbol_wrapper.symbol}


class DifferentialAssignment(Assignment):
    # def __init__(self, variable, expression):
    #     super().__init__(variable, expression)
        # self.variable = variable    # has a symbol, description, initial value
        # self.expression = expression

    @property
    def variable(self):
        return self.symbol_wrapper

    def to_sim_variable(self, variables=Variables(), parameters=Parameters()):
        var = SimVariable(self.variable)
        var.set_update_rule(SimUpdateRule.from_update_rule(UpdateRule(var, self.expression, variables, parameters), variables, parameters))
        return var

    def combine(self, other):
        assert self.variable.symbol == other.variable.symbol
        # TODO: check description and initial value
        self.expression += other.expression


class ParameterAssignment(Assignment):

    @property
    def parameter(self):
        return self.symbol_wrapper

    def to_sim_parameter(self, variables=Variables(), parameters=Parameters()):
        var = SimParameter(self.parameter)
        var.set_update_rule(SimUpdateRule.from_update_rule(UpdateRule(var, self.expression, variables, parameters), variables, parameters))
        return var


class IdentificationAssignment(ParameterAssignment):

    def __init__(self, parameter, other_parameter):
        if type(other_parameter) is str:
            other_parameter = sym.Symbol(other_parameter)
        super().__init__(parameter, other_parameter)

    # Assignment where the RHS is simply another symbol
    pass


class Port:
    def __init__(self, name, description=""):
        if HIERARCHY_SEPARATOR in name:
            raise ValueError(f"Port '{name}': Port names must not contain '{HIERARCHY_SEPARATOR}'.")
        self.name = name
        self.description = description


class VariablePort(Port):
    pass

class InputPort(Port):
    def __init__(self, name, description="", default_value=None):
        super().__init__(name, description)
        self.default_value = default_value

class OutputPort(Port):
    pass


class CompiledPort:
    # Note: For input ports, their compilation result will initially have None
    # on the RHS of the assignment. This will be overwritten once the port
    # received an edge coming into it from the outside.
    def __init__(self, port, assignment):
        '''
        port: the original port this was compiled from
        assignment: associated assignment
        '''
        self.port = port
        self.name = port.name
        self.assignment = assignment

class CompiledVariablePort(CompiledPort):

    def to_sim_variable(self, variables=Variables(), parameters=Parameters()):
        # This is only for compiled variable ports.
        return self.assignment.to_sim_variable(variables, parameters)


class CompiledParameterPort(CompiledPort):

    def to_sim_parameter(self, variables=Variables(), parameters=Parameters()):
        return self.assignment.to_sim_parameter(variables, parameters)


class CompiledInputPort(CompiledParameterPort):
    def __init__(self, port, assignment, default_value=None):
        super().__init__(port, assignment)
        self.default_value = default_value


class CompiledOutputPort(CompiledParameterPort):
    pass


class PortedObject(ABC):

    def __init__(self, name: str):
        self.name = name
        # Ports exposed to the outside, indexed by their name (str)
        self.variable_ports = {}
        self.input_ports = {}
        self.output_ports = {}

    def check_existing_port_names(self, port: Port):
        if port.name in self.variable_ports or port.name in self.output_ports or port.name in self.variable_ports:
            raise ValueError(f"Port with name '{port.name}' doubly defined in PortedObject '{self.name}'.")

    def add_input_port(self, port: Port):
        self.check_existing_port_names(port)
        self.input_ports[port.name] = port

    def add_output_port(self, port: Port):
        self.check_existing_port_names(port)
        self.output_ports[port.name] = port

    def add_variable_port(self, port: Port):
        self.check_existing_port_names(port)
        self.variable_ports[port.name] = port

    def get_port_by_name(self, port: str):
        if port in self.variable_ports:
            return self.variable_ports[port]
        if port in self.input_ports:
            return self.input_ports[port]
        if port in self.output_ports:
            return self.output_ports[port]
        return None

    @abstractmethod
    def compile(self):
        pass


class CompositePortedObject(PortedObject):
    '''
    Validation (TODO)

    Errors:
        Every input port of a child must have at most one edge into it
        Every output port must be the destination of exactly one directed wire
        Every variable port needs to be connected as a destination (parent)
            of a VariableAggregationWiring, exactly once
            (unless this is a VariablePortedObject: then no connection)

    Warnings:
        Every input port should be the source of at least one directed edge
        The directed wires should have no cycles (when contracting child ported objects into nodes of a graph)
        Every output port of a child should have an edge going out of it
        Every output port of a child should have a VariableAggregationWiring going out of it
    '''

    def __init__(self, name):
        super().__init__(name)
        self.children = {}
        self.variable_aggregation_wiring = []
        self.directed_wires = []

    def is_own_port(self, name: str):
        if HIERARCHY_SEPARATOR in name:
            return False
        return True

    def add_child(self, child):
        self.children[child.name] = child

    def add_directed_wire(self, source_name: str, destination_name: str):
        # These are be names of ports
        source_port = self.get_port_by_name(source_name)
        if source_port is None:
            raise WiringError(f"Incorrect wiring in '{self.name}'. Destination port '{source_name}' does not exist.")
        if source_name in self.output_ports or source_name in self.variable_ports or (source_name not in self.input_ports and type(source_port) is InputPort):
            # Source must be: own input, or child output, or child variable
            raise WiringError(f"Incorrect wiring in '{self.name}'. Destination port '{source_name}' must be an input port or a child output/variable port.")

        destination_port = self.get_port_by_name(destination_name)
        if destination_port is None:
            raise WiringError(f"Incorrect wiring in '{self.name}'. Destination port '{destination_name}' does not exist.")
        if destination_name in self.input_ports or destination_name in self.variable_ports or (destination_name not in self.output_ports and type(destination_port) is not InputPort):
            # Destination must be: own output, or child input
            raise WiringError(f"Incorrect wiring in '{self.name}'. Destination port '{destination_name}' must be an output port or a child input port.")

        wire = DirectedWire(source_name, destination_name)
        self.directed_wires.append(wire)

    def add_variable_aggregation_wiring(self, child_ports: List[str], parent_port: str):
        # These are names of ports
        # For convenienice, we should probably create the parent_port in the process.
        # All ports must be variable ports.
        # Parent port should be port of the object itself
        port = self.get_port_by_name(parent_port)
        if port is None or not type(port) is VariablePort or not self.is_own_port(parent_port):
            WiringError(f"Incorrect wiring in '{self.name}'. Parent port '{parent_port}' must be a variable port of the ported object itself.")
        # Child ports should be ports of children
        for child_port in child_ports:
            port = self.get_port_by_name(child_port)
            if port is None or not type(port) is VariablePort or self.is_own_port(child_port):
                WiringError(f"Incorrect wiring in '{self.name}'. Child port '{child_port}' must be a variable port of a child.")
        wiring = VariableAggregationWiring(child_ports, parent_port)
        self.variable_aggregation_wiring.append(wiring)

    def get_port_by_name(self, port_name):
        port = super().get_port_by_name(port_name)
        if port is not None:
            return port
        parts = port_name.split(HIERARCHY_SEPARATOR, 1)
        if len(parts) == 1:
            raise ValueError(f"Port '{port_name}' in ported object '{self.name}' not found.")
        parent, name = parts
        if parent not in self.children:
            raise ValueError(f"Port parent '{parent}' of '{port_name}' not found in ported object '{self.name}'.")
        return self.children[parent].get_port_by_name(name)

    def compile(self):
        # Approach 1:
        # Assume: no cycles in the in/out ports
        # do topological sort on subsystems wrt directed edges connection i/o ports
        # go through children in order
        # before each: infer input values
        # compile subsystem with these
        # compute outputs
        compiled = CompiledPortedObject(self.name)
        compiled.children = {name : child.compile() for name, child in self.children.items()}

        # For each child input port, we have to ensure it's connected or has a default value

        # Collect all child input ports
        child_input_ports = {}
        for child_name, child in self.children.items():
            for name, port in child.input_ports.items():
                new_name = HIERARCHY_SEPARATOR.join([child_name, name])
                child_input_ports[new_name] = port

        # Process child input ports with incoming wires
        for wire in self.directed_wires:
            if wire.destination_port in child_input_ports:
                source = self.get_port_by_name(wire.source_port)
                destination = self.get_port_by_name(wire.destination_port)
                assert type(destination) is InputPort
                assg = IdentificationAssignment(wire.destination_port, wire.source_port)
                if self.is_own_port(wire.source_port):
                    # Goes from own input port to child input port.
                    self.input_ports[source.name] = CompiledInputPort(source, assg, source.default_value)
                else:
                    # Goes from child output port to child input port.
                    compiled.internal_parameter_assignments.append(assg)
                child_input_ports.pop(wire.destination_port)
            elif wire.destination_port in self.output_ports:
                source = self.get_port_by_name(wire.source_port)
                destination = self.get_port_by_name(wire.destination_port)
                assert type(destination) is OutputPort
                if self.is_own_port(wire.source_port):
                    # Goes from own input port to own output port.
                    # We create a compiled input and a compiled output port, each
                    # with an assignment. So we need an intermediary temp parameter
                    temp_param = f"temp_{wire.source_port}_{wire.destination_port}"
                    assg_in = IdentificationAssignment(temp_param, wire.source_port)
                    assg_out = IdentificationAssignment(wire.destination_port, temp_param)
                    self.input_ports[source.name] = CompiledInputPort(source, assg_in, source.default_value)
                    self.output_ports[destination.name] = CompiledOutputPort(destination, assg_out)
                else:
                    # Goes from child output/variable port to own output port.
                    # We create a compiled output port
                    assg = IdentificationAssignment(wire.destination_port, wire.source_port)
                    self.output_ports.append(CompiledOutputPort(source, assg))
                    compiled.internal_parameter_assignments.append(assg)
            else:
                raise WiringError(f"Incorrect wiring in '{self.name}'. DirectedWire destination should be output port or child input port but is {wire.destination_port}")

        # Find unconnected child input ports and check for default values
        bad_input_ports = []
        for name, port in child_input_ports.items():
            if port.default_value is None:
                bad_input_ports.append(name)
            else:
                # Initialize their parameters with initial values
                assg = ParameterAssignment(name, port.default_value)
                compiled.internal_parameter_assignments.append(assg)
        if bad_input_ports:
            raise WiringError(f"Incorrect wiring in '{self.name}'. The following child input ports are unconnected and have no default value: {bad_input_ports}")

        # TODO: Warn if there is a variable port that is not connected to children
        compiled.variable_ports = {}
        for wiring in self.variable_aggregation_wiring:
            parent = self.get_port_by_name(wiring.parent_port)
            child_ports = [compiled.get_port_by_name(c) for c in wiring.child_ports]
            assg = deepcopy(child_ports[0].assignment)
            for child in child_ports[1:]:
                assg.combine(child.assignment)
            new_port = CompiledVariablePort(parent, assg)
            compiled.variable_ports[parent.name] = new_port

        return compiled


class VariablePortedObject(PortedObject):
    # This ported object contains the information about a single variable

    def __init__(self, name, assignments=None):
        # Note: assignment includes all information about the variable
        super().__init__(name)
        self.assignments = {}
        if assignments is not None:
            for assignment in assignments:
                self.add_variable_assignment(assignment)
        # TODO: Create input ports for parameters
        # self.input_ports

    def add_variable_assignment(self, assignment):
        variable_name = str(assignment.variable.symbol)
        if variable_name in self.variable_ports:
            raise ValueError(f"Variable '{variable_name}' in VariablePortedObject '{self.name}' doubly defined.")
        self.assignments[variable_name] = assignment
        self.variable_ports[variable_name] = VariablePort(variable_name)

    def assert_no_undefined_symbols(self, global_symbols):
        variable_symbols = set()
        all_assignment_symbols = set()
        parameter_symbols = set()
        for port in self.input_ports.values():
            parameter_symbols.add(sym.sympify(port.name))
        for assignment in self.assignments.values():
            variable_symbols.add(assignment.variable.symbol)
            assignment_symbols = sym.sympify(assignment.expression).free_symbols
            all_assignment_symbols |= assignment_symbols
        all_symbols = variable_symbols | parameter_symbols | global_symbols
        if not all_assignment_symbols.issubset(all_symbols):
            undefined_symbols = all_assignment_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in assignment of ported object {self.name}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}. Consider adding input ports for these."
            )

    def compile(self, global_symbols=set()):
        self.assert_no_undefined_symbols(global_symbols)
        compiled = CompiledPortedObject(self.name)
        # compiled.input_ports = self.input_ports
        compiled.variable_ports = {
            variable_name : CompiledVariablePort(original_port, self.assignments[variable_name])
            for variable_name, original_port in self.variable_ports.items()
        }
        return compiled


class FunctionalPortedObject(PortedObject):
    def __init__(self, name):
        super().__init__(name)
        self.assignments = {}

    def add_assignment(self, assignment):
        # new output port for the RHS
        # input ports for the free parameters on the LHS
        pass

    def compile(self):
        pass


class CompiledPortedObject(CompositePortedObject):
    def __init__(self, name):
        super().__init__(name)
        # free input parameters and (possibly) their default values
        self.input_ports = {}
        # values of output parameters in terms of input parameters
        self.output_ports = {}
        # ODEs of variables in terms of input parameters and other variables
        self.variable_ports = {}
        # TODO: ODEs of unexposed variables in terms of other parameters and variables
        # --> SimVariable
        self.internal_variable_assignments = []
        # Parameters that are initialized via default parameters, and whose values are fully determined
        self.internal_parameter_assignments = []
        # LinearAggregatorWiring
        # map from names to full names
        # parameters and variables

    def set_input_parameters(self, parameter_assignments=[]):
        # TODO: Make this non-destructive so we can run a simulation with different inputs
        # without full recompilation
        assg_dict = {}
        for assg in parameter_assignments:
            print(str(assg.parameter.symbol))
            assg_dict[str(assg.parameter.symbol)] = assg
        for name, port in self.input_ports.items():
            if name in assg_dict:
                self.internal_parameter_assignments.append(assg_dict[name])
            elif port.default_value is not None:
                new_assg = ParameterAssignment(name, port.default_value)
                self.internal_parameter_assignments.append(new_assg)
            else:
                raise ValueError(f"Undefined input parameter: {name}")
        self.input_ports = {}

    def get_simvariablesparameters(self):
        # print(self.internal_parameter_assignments[0].parameter)

        variables = []
        for port in self.variable_ports.values():
            variables.append(port.assignment.variable)
        variables = Variables(variables)

        self.set_input_parameters()
        parameters = []
        for assg in self.internal_parameter_assignments:
            parameters.append(Parameter(assg.parameter, assg.expression))
        parameters = Parameters(parameters)

        simvariables = []
        for port in self.variable_ports.values():
            simvariables.append(port.to_sim_variable(variables))

        simparameters = []
        for assg in self.internal_parameter_assignments:
            simparameters.append(assg.to_sim_parameters(variables, parameters))

        return Variables(simvariables), Parameters(simparameters)


class VariableAggregationWiring:
    def __init__(self, child_ports, parent_port):
        self.child_ports = child_ports
        self.parent_port = parent_port


class DirectedWire:
    def __init__(self, source_port, destination_port):
        self.source_port = source_port
        self.destination_port = destination_port
        # needs to indicate whether own port or child port


# from input port to output port
# from variable port to output port
# LinearAggregatorWiring: from set of variable ports to variable

# VariablePort
# incoming connection
# outgoing connection
# IOPort
