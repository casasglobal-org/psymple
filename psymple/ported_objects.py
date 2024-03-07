from abc import ABC, abstractmethod
import itertools
from typing import List
from operator import attrgetter

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

HIERARCHY_SEPARATOR = "."


class WiringError(Exception):
    pass


class Assignment:
    def __init__(self, symbol_wrapper, expression):
        '''
        symbol_wrapper: LHS of the assignment (e.g. parameter or variable)
            If input is a string, it is converted to a symbol_wrapper.
        expression: expression on the RHS.
            If input is a string, it is converted to a sympy expression.
        '''
        if type(symbol_wrapper) is str:
            symbol_wrapper = SymbolWrapper(sym.Symbol(symbol_wrapper))
        elif type(symbol_wrapper) is sym.Symbol:
            symbol_wrapper = SymbolWrapper(symbol_wrapper)
        self.symbol_wrapper = symbol_wrapper
        if type(expression) in [str, float, int]:
            expression = sym.sympify(expression)
        self.expression = expression

    @property
    def symbol(self):
        return self.symbol_wrapper.symbol

    @property
    def name(self):
        return self.symbol_wrapper.name

    def substitute_symbol(self, old_symbol, new_symbol):
        if self.symbol == old_symbol:
            self.symbol_wrapper.symbol = new_symbol
        self.expression = self.expression.subs(old_symbol, new_symbol)

    def get_free_symbols(self, global_symbols=set()):
        assignment_symbols = self.expression.free_symbols
        return assignment_symbols - global_symbols - {self.symbol_wrapper.symbol}


class DifferentialAssignment(Assignment):
    # TODO: Ensure we that the symbol_wrapper is instance of Variable.
    # def __init__(self, variable, expression):
    #     super().__init__(variable, expression)
    # self.variable = variable    # has a symbol, description, initial value
    # self.expression = expression

    @property
    def variable(self):
        return self.symbol_wrapper

    def to_sim_variable(self, variables=Variables(), parameters=Parameters()):
        '''
        Convert to a version of variable that is used in the Simulation.

        variables/parameters: stuff that may appear on the RHS of the assignment.
        TODO: This specific implementation is a relic from the System implementation from
        before and should probably be streamlined.
        '''
        var = SimVariable(self.variable)
        var.set_update_rule(
            SimUpdateRule.from_update_rule(
                UpdateRule(var, self.expression, variables, parameters),
                variables,
                parameters,
            )
        )
        return var

    def combine(self, other):
        # TODO: check description and initial value for consistency
        # print(self.variable.symbol, other.variable.symbol)
        # assert self.variable.symbol == other.variable.symbol
        # TODO: Check if we want to mutate this assignment, or rather produce a new one
        self.expression += other.expression

    def combine_and_substitute(self, other):
        # Takes two assignments and adds up their expressions.
        # If the variable symbols are different, the first variable
        # is retained, and instances of the second in its expression
        # are replaced by the first.

        other_expression = other.expression
        if self.variable.symbol != other.variable.symbol:
            other_expression = other_expression.subs(other.variable.symbol, self.variable.symbol)
        # TODO: Check if we want to mutate this assignment, or rather produce a new one
        self.expression += other_expression


class ParameterAssignment(Assignment):
    # TODO: Ensure we that the symbol_wrapper is instance of Parameter.

    @property
    def parameter(self):
        return self.symbol_wrapper

    def to_sim_parameter(self, variables=Variables(), parameters=Parameters()):
        '''
        Convert to a version of variable that is used in the Simulation.

        variables/parameters: stuff that may appear on the RHS of the assignment.
        TODO: This specific implementation is a relic from the System implementation from
        before and should probably be streamlined.
        '''
        var = SimParameter(self.parameter)
        var.set_update_rule(
            SimUpdateRule.from_update_rule(
                UpdateRule(var, self.expression, variables, parameters),
                variables,
                parameters,
            )
        )
        return var


class SymbolIdentification:
    '''
    Identify two symbols as equal
    '''

    def __init__(self, new_symbol, old_symbol):
         self.old_symbol = old_symbol
         self.new_symbol = new_symbol


class Port:
    """
    Ports currently only have a name that can be referenced by the wirings.

    The name uniquely determines the port's symbol.

    The symbol only has relevance in two cases:
    - Input port symbols for VariablePortedObjects and FunctionalPortedObjects:
        In this case, the symbol may appear in expressions defined within those
        objects, and input values will be substituted into it.
    - Variable port symbols when the variable port is not connected on the outside
        This symbol will then become globally associated to the variable that is
        simulated in the system
    """

    def __init__(self, name, description=""):
        if HIERARCHY_SEPARATOR in name:
            raise ValueError(
                f"Port '{name}': Port names must not contain '{HIERARCHY_SEPARATOR}'."
            )
        self.name = name
        self.description = description

    @property
    def symbol(self):
        return sym.Symbol(self.name)


class VariablePort(Port):
    pass


class InputPort(Port):
    def __init__(self, name, description="", default_value=None):
        super().__init__(name, description)
        self.default_value = default_value


class OutputPort(Port):
    pass


class CompiledPort(Port):
    def __init__(self, port, assignment):
        self.name = port.name
        self.description = port.description
        self.assignment = deepcopy(assignment)

    def substitute_symbol(self, old_symbol, new_symbol):
        self.assignment.substitute_symbol(old_symbol, new_symbol)
        # In case the symbol of this port itself was substituted,
        # this will be reflected in the assignment, and we can pull
        # the updated name from there.
        self.name = self.assignment.name


class CompiledVariablePort(CompiledPort):
    def to_sim_variable(self, variables=Variables(), parameters=Parameters()):
        return self.assignment.to_sim_variable(variables, parameters)


class CompiledOutputPort(CompiledPort):
    def to_sim_parameter(self, variables=Variables(), parameters=Parameters()):
        return self.assignment.to_sim_parameter(variables, parameters)


class CompiledInputPort(CompiledPort):
    def __init__(self, port):
        assert isinstance(port, InputPort)
        super().__init__(port, None)
        self.default_value = port.default_value

    def substitute_symbol(self, old_symbol, new_symbol):
        if self.symbol == old_symbol:
            self.name = str(new_symbol)


class PortedObject(ABC):
    def __init__(self, name: str):
        self.name = name
        # Ports exposed to the outside, indexed by their name (str)
        self.variable_ports = {}
        self.input_ports = {}
        self.output_ports = {}

    def check_existing_port_names(self, port: Port):
        if (
            port.name in self.variable_ports
            or port.name in self.output_ports
            or port.name in self.variable_ports
        ):
            raise ValueError(
                f"Port with name '{port.name}' doubly defined in PortedObject '{self.name}'."
            )

    def add_input_port(self, port: InputPort):
        # assert isinstance(port, InputPort)
        self.check_existing_port_names(port)
        self.input_ports[port.name] = port

    def add_output_port(self, port: OutputPort):
        # assert isinstance(port, OutputPort)
        self.check_existing_port_names(port)
        self.output_ports[port.name] = port

    def add_variable_port(self, port: VariablePort):
        # assert isinstance(port, VariablePort)
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
    def compile(self, prefix_names=False):
        pass


class ODECreatorPortedObject(PortedObject):
    def __init__(self):
        self.input_ports # expr, variable
        self.variable_ports # output

    def compile(self, global_symbols=set()):
        # d var / d t = expression
        # if the input variable name differs from the port,
        # create an identification assignment
        pass


class RHSExpressionPortedObject(PortedObject):
    # A variable comes in, an expression comes out
    def __init__(self):
        self.input_ports # expr, variable
        self.output_ports # output

    def compile(self, global_symbols=set()):
        # assert that the input is a variable
        # output = input.rhs
        pass


class OperatorPortedObject(PortedObject):
    # abstract class
    def __init__(self, input_port_names, output_port_name):
        pass


class PlusOperatorPortedObject(OperatorPortedObject):

    def compile(self, global_symbols=set()):
        # Make an assignment that sums up the input
        pass


class VariablePortedObject(PortedObject):
    """
    A PortedObject containing a collection of ODEs (DifferentialAssignments).

    Each ODE is associated to a variable, which may or may not be exposed as a variable port.
    Symbols on the RHS of the ODE should be either:
    - Variables defined in this ported object
    - parameters that have corresponding input ports
    - globally defined symbols

    TODO: Implement the above.
    """

    def __init__(self, name: str, assignments: List[Assignment] = [], expose_ports=True):
        super().__init__(name)
        # A dict of assignments indexed by the variable name
        self.assignments = {}
        for assignment in assignments:
            self.add_variable_assignment(assignment, expose_ports)
        # TODO: Create input ports for parameters?
        # We can do this automatically (no default values then),
        # or issue errors if the ports are missing.

    def add_variable_assignment(self, assignment, expose_port=True):
        variable_name = str(assignment.variable.symbol)
        if variable_name in self.assignments:
            raise ValueError(
                f"Variable '{variable_name}' in VariablePortedObject '{self.name}' doubly defined."
            )
        self.assignments[variable_name] = assignment
        if expose_port:
            # TODO: Is there a use case where the variable name is different from the port name?
            self.variable_ports[variable_name] = VariablePort(variable_name)

    def assert_no_undefined_symbols(self, global_symbols=set()):
        variable_symbols = set()
        all_assignment_symbols = set()
        parameter_symbols = set()
        for name, port in self.input_ports.items():
            parameter_symbols.add(port.symbol)
        for assignment in self.assignments.values():
            variable_symbols.add(assignment.variable.symbol)
            assignment_symbols = assignment.get_free_symbols()
            all_assignment_symbols |= assignment_symbols
        all_symbols = variable_symbols | parameter_symbols | global_symbols
        if not all_assignment_symbols.issubset(all_symbols):
            undefined_symbols = all_assignment_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in assignment of ported object {self.name}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}. Consider adding input ports for these."
            )

    def compile(self, prefix_names=False, global_symbols=set()):
        self.assert_no_undefined_symbols(global_symbols)
        compiled = CompiledPortedObject(self.name)
        for variable_name, assignment in self.assignments.items():
            if variable_name in self.variable_ports:
                compiled.variable_ports[variable_name] = CompiledVariablePort(
                    self.variable_ports[variable_name], self.assignments[variable_name]
                )
            else:
                compiled.internal_variable_assignments[variable_name] = assignment

        for input_port in self.input_ports.values():
            compiled.add_input_port(CompiledInputPort(input_port))

        if prefix_names:
            compiled.sub_prefixed_symbols()
        return compiled


class SymbolPortedObject(VariablePortedObject):
    def __init__(self, name: str):
        assignment = DifferentialAssignment(name, 0)
        super().__init__(name, [assignment])


class FunctionalPortedObject(PortedObject):
    """
    A PortedObject modeling a function.

    The function is defined by a set of assignments.

    The function arguments are the free parameters on the RHS of the assignments,
    and should be exposed as input ports. The function values are the LHS of the
    assignments, and should be exposed as input ports.

    TODO: In the future, this should be a composite ported object that
    decomposes its assignments into a sequence of OperatorPortedObjects.

    TODO: Any nuances to this?

    TODO: Implement this.
    """

    def __init__(
            self,
            name: str,
            input_ports: List[InputPort] = [],
            assignments: List[Assignment] = [],
            create_input_ports=False,
        ):
        super().__init__(name)
        # A dict of assignments indexed by the variable name
        self.assignments = {}
        for input_port in input_ports:
            self.add_input_port(input_port)
        for assignment in assignments:
            self.add_assignment(assignment, create_input_ports)
        # TODO: Create input ports for parameters?
        # We can do this automatically (no default values then),
        # or issue errors if the ports are missing.

    def add_assignment(self, assignment, create_input_ports=False):
        parameter_name = str(assignment.parameter.symbol)
        if parameter_name in self.assignments:
            raise ValueError(
                f"Variable '{parameter_name}' in VariablePortedObject '{self.name}' doubly defined."
            )
        free_symbols = assignment.get_free_symbols()
        for symbol in free_symbols:
            name = str(symbol)
            if name not in self.input_ports:
                if create_input_ports:
                    self.input_ports.append(InputPort(name))
                else:
                    raise ValueError(
                        f"Expression contains symbol {name} but there is no "
                        "corresponding input port."
                    )
        self.assignments[parameter_name] = assignment
        self.output_ports[parameter_name] = OutputPort(parameter_name)

    def compile(self, prefix_names=False, global_symbols=set()):
        compiled = CompiledPortedObject(self.name)
        # ParameterAssignment()
        # self.internal_parameter_assignments = {}
        for name, input_port in self.input_ports.items():
            compiled.input_ports[name] = CompiledInputPort(input_port)
        for name, output_port in self.output_ports.items():
            assignment = self.assignments[name]
            compiled.output_ports[name] = CompiledOutputPort(
                output_port, assignment
            )
        if prefix_names:
            compiled.sub_prefixed_symbols()
        return compiled


class CompositePortedObject(PortedObject):
    """

    A PortedObject composed of child ported objects that are wired together.

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
    """

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
        source_port = self.get_port_by_name(source_name)
        if source_port is None:
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                f"Destination port '{source_name}' does not exist."
            )
        if (
            source_name in self.output_ports
            or source_name in self.variable_ports
            or (source_name not in self.input_ports and type(source_port) is InputPort)
        ):
            # Source must be: own input, or child output, or child variable
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. Destination port '{source_name}' "
                "must be an input port or a child output/variable port."
            )

        destination_port = self.get_port_by_name(destination_name)
        if destination_port is None:
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                f"Destination port '{destination_name}' does not exist."
            )
        if (
            destination_name in self.input_ports
            or destination_name in self.variable_ports
            or (
                destination_name not in self.output_ports
                and type(destination_port) is not InputPort
            )
        ):
            # Destination must be: own output, or child input
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                f"Destination port '{destination_name}' must be "
                "an output port or a child input port."
            )

        wire = DirectedWire(source_name, destination_name)
        self.directed_wires.append(wire)

    def add_variable_aggregation_wiring(
        self,
        child_ports: List[str],
        parent_port: str = None,
        output_name: str = None,
    ):
        # TODO: This should become reimplemented by using a composite
        # ported object that contains building blocks modeling this behavior.
        # These are names of ports
        # All ports must be variable ports.
        # Parent port (if provided) should be port of the object itself
        if parent_port is not None:
            port = self.get_port_by_name(parent_port)
            if (
                port is None
                or not type(port) is VariablePort
                or not self.is_own_port(parent_port)
            ):
                WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    f"Parent port '{parent_port}' must be a variable port "
                    "of the ported object itself."
                )
        # Child ports should be ports of children
        for child_port in child_ports:
            port = self.get_port_by_name(child_port)
            if (
                port is None
                or not type(port) is VariablePort
                or self.is_own_port(child_port)
            ):
                WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    f"Child port '{child_port}' must be a variable port of a child."
                )
        wiring = VariableAggregationWiring(child_ports, parent_port, output_name)
        self.variable_aggregation_wiring.append(wiring)

    def get_port_by_name(self, port_name: str):
        port = super().get_port_by_name(port_name)
        if port is not None:
            return port
        parts = port_name.split(HIERARCHY_SEPARATOR, 1)
        if len(parts) == 1:
            raise ValueError(
                f"Port '{port_name}' in ported object '{self.name}' not found."
            )
        parent, name = parts
        if parent not in self.children:
            raise ValueError(
                f"Port parent '{parent}' of '{port_name}' not found "
                f"in ported object '{self.name}'."
            )
        return self.children[parent].get_port_by_name(name)

    def compile(self, prefix_names=False):
        # Approach 1:
        # Assume: no cycles in the in/out ports
        # do topological sort on subsystems wrt directed edges connection i/o ports
        # go through children in order
        # before each: infer input values
        # compile subsystem with these
        # compute outputs
        compiled = CompiledPortedObject(self.name)
        compiled.children = {
            name: child.compile(True) for name, child in self.children.items()
        }

        # For each child input port, we have to ensure it's connected or has a default value

        # Collect all child input ports
        child_input_ports = {}
        for child_name, child in self.children.items():
            for name, port in child.input_ports.items():
                new_name = HIERARCHY_SEPARATOR.join([child_name, name])
                child_input_ports[new_name] = port

        for name, input_port in self.input_ports.items():
            compiled.input_ports[name] = CompiledInputPort(input_port)

        # Process child input ports with incoming wires
        for wire in self.directed_wires:
            if wire.destination_port in child_input_ports:
                # Goes from own input or child output port to child input port.
                source = self.get_port_by_name(wire.source_port)
                destination = self.get_port_by_name(wire.destination_port)
                assert type(destination) is InputPort
                assg = SymbolIdentification(destination.symbol, source.symbol)
                compiled.symbol_identifications.append(assg)
                child_input_ports.pop(wire.destination_port)
            elif wire.destination_port in self.output_ports:
                source = self.get_port_by_name(wire.source_port)
                destination = self.get_port_by_name(wire.destination_port)
                assert type(destination) is OutputPort
                if self.is_own_port(wire.source_port):
                    # Goes from own input port to own output port.
                    # I don't see a use case for this.
                    assg_out = ParameterAssignment(destination.symbol_wrapper, source.symbol)
                    compiled.output_ports[destination.name] = CompiledOutputPort(
                        destination, assg_out
                    )
                    assert False
                else:
                    # Goes from child output/variable port to own output port.
                    # We create a compiled output port
                    assg = ParameterAssignment(destination.symbol_wrapper, source.symbol)
                    compiled.output_ports.append(CompiledOutputPort(source, assg))
                    compiled.symbol_identifications.append(assg)
            else:
                raise WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    "DirectedWire destination should be output port "
                    f"or child input port but is {wire.destination_port}"
                )

        # Find unconnected child input ports and check for default values
        bad_input_ports = []
        for name, port in child_input_ports.items():
            if port.default_value is None:
                bad_input_ports.append(name)
            else:
                # Initialize their parameters with initial values
                assg = ParameterAssignment(SymbolWrapper(port.symbol), port.default_value)
                compiled.internal_parameter_assignments[name] = assg
        if bad_input_ports:
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                "The following child input ports are unconnected "
                f"and have no default value: {bad_input_ports}"
            )

        # TODO: Warn if there is a variable port that is not connected to children
        compiled.variable_ports = {}
        for wiring in self.variable_aggregation_wiring:
            child_ports = [compiled.get_port_by_name(c) for c in wiring.child_ports]
            values = {c.assignment.variable.initial_value for c in child_ports} - {None}
            if len(values) > 1:
                raise ValueError(f"Inconsistent initial values for variable {wiring.parent_port}: {values}.")
            elif values:
                value = values.pop()
            else:
                value = None

            if wiring.parent_port is not None:
                new_var = Variable(wiring.parent_port, value)
            elif wiring.output_name is not None:
                new_var = Variable(wiring.output_name, value)
            else:
                raise WiringError(
                    f"For VariableAggregationWiring, either parent_port "
                    "or output_name need to be provided"
                )
            assg = DifferentialAssignment(new_var, "0")
            for child in child_ports:
                assg.combine(child.assignment)
                compiled.symbol_identifications.append(
                    SymbolIdentification(new_var.symbol, child.assignment.symbol)
                )
            if wiring.parent_port is not None:
                parent = self.get_port_by_name(wiring.parent_port)
                new_port = CompiledVariablePort(parent, assg)
                compiled.variable_ports[parent.name] = new_port
            else:
                compiled.internal_variable_assignments[new_var] = assg

        compiled.sub_symbol_identifications()
        if prefix_names:
            compiled.sub_prefixed_symbols()
        return compiled


class CompiledPortedObject(CompositePortedObject):
    def __init__(self, name):
        super().__init__(name)
        # free input parameters and (possibly) their default values
        self.input_ports = {}
        # values of output parameters in terms of input parameters
        self.output_ports = {}
        # ODEs of variables in terms of input parameters and other variables
        self.variable_ports = {}
        # ODEs of unexposed variables in terms of other parameters and variables
        self.internal_variable_assignments = {}
        # Parameters that are initialized via default parameters, and whose values are fully determined
        self.internal_parameter_assignments = {}

        # Equivalent symbols
        self.symbol_identifications = []

    def sub_symbol_identifications(self):
        # Substitute equivalent symbols by a representative
        # TODO: Cycle detection
        for symbol_identification in self.symbol_identifications:
            self.sub_everywhere(symbol_identification.old_symbol, symbol_identification.new_symbol)

    def get_all_symbol_containers(self):
        return itertools.chain(
            self.input_ports.items(),
            self.output_ports.items(),
            self.variable_ports.items(),
            self.internal_variable_assignments.items(),
            self.internal_parameter_assignments.items(),
        )

    def sub_prefixed_symbols(self):
        '''
        Replaces all non-global symbols by adding the compiled object's
        name as a prefix.

        This is done in both the LHS and RHS of the assignments, however,
        the dictionary keys are NOT affected.
        '''
        for name, symbol_container in self.get_all_symbol_containers():
            assert name == symbol_container.name
            old_symbol = symbol_container.symbol
            new_symbol = sym.Symbol(HIERARCHY_SEPARATOR.join([self.name, name]))
            self.sub_everywhere(old_symbol, new_symbol)

    def sub_everywhere(self, old_symbol, new_symbol):
        assert isinstance(old_symbol, sym.Symbol)
        assert isinstance(new_symbol, sym.Symbol)
        for name, symbol_container in self.get_all_symbol_containers():
            symbol_container.substitute_symbol(old_symbol, new_symbol)

    def set_input_parameters(self, parameter_assignments=[]):
        # TODO: Make this non-destructive so we can run a simulation with different inputs
        # without full recompilation
        assg_dict = {}
        for assg in parameter_assignments:
            # print(str(assg.parameter.symbol))
            assg_dict[str(assg.parameter.symbol)] = assg
        for name, port in self.input_ports.items():
            if name in assg_dict:
                self.internal_parameter_assignments[name] = assg_dict[name]
            elif port.default_value is not None:
                new_assg = ParameterAssignment(name, port.default_value)
                self.internal_parameter_assignments[name] = new_assg
            else:
                raise ValueError(f"Undefined input parameter: {name}")
        self.input_ports = {}

    def get_simvariablesparameters(self):
        variables = []
        for port in self.variable_ports.values():
            variables.append(port.assignment.variable)
        variables = Variables(variables)

        self.set_input_parameters()
        parameters = []
        for assg in self.internal_parameter_assignments.values():
            parameters.append(Parameter(assg.parameter, assg.expression))
        parameters = Parameters(parameters)

        simvariables = []
        for port in self.variable_ports.values():
            simvariables.append(port.to_sim_variable(variables))

        simparameters = []
        for assg in self.internal_parameter_assignments.values():
            simparameters.append(assg.to_sim_parameters(variables, parameters))

        return Variables(simvariables), Parameters(simparameters)


class VariableAggregationWiring:
    # TODO: This should become obsolete. Instead, we will have a composite
    # ported object that contains building blocks modeling this behavior
    def __init__(self, child_ports: str, parent_port: str, output_name: str):
        self.child_ports = child_ports
        self.parent_port = parent_port
        self.output_name = output_name


class DirectedWire:
    def __init__(self, source_port: str, destination_port: str):
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
