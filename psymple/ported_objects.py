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
    SimParameter,
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
        """
        symbol_wrapper: LHS of the assignment (e.g. parameter or variable)
            If input is a string, it is converted to a symbol_wrapper.
        expression: expression on the RHS.
            If input is a string, it is converted to a sympy expression.
        """
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

    # def substitute_parameter_assignments(self, parameter_assignments):
    #     substitutions = [
    #         (assg.symbol, assg.expression) for assg in parameter_assignments
    #     ]
    #     self.equation = self.equation.subs(substitutions)

    def get_free_symbols(self, global_symbols=set()):
        assignment_symbols = self.expression.free_symbols
        return assignment_symbols - global_symbols - {self.symbol_wrapper.symbol}

    def to_update_rule(self, variables=Variables(), parameters=Parameters()):
        """
        Convert to UpdateRules so that it can be used in the Simulation.

        variables/parameters: stuff that may appear on the RHS of the assignment.
        TODO: This specific implementation is a relic from the System implementation from
        before and should probably be streamlined.
        """
        return UpdateRule(self.symbol_wrapper, self.expression, variables, parameters)

    def __repr__(self):
        return f"{type(self).__name__} {self.name} = {self.expression}"


class DifferentialAssignment(Assignment):
    # TODO: Ensure we that the symbol_wrapper is instance of Variable.
    # def __init__(self, variable, expression):
    #     super().__init__(variable, expression)
    # self.variable = variable    # has a symbol, description, initial value
    # self.expression = expression

    @property
    def variable(self):
        return self.symbol_wrapper

    def __repr__(self):
        return f"DifferentialAssignment d({self.name})/dt = {self.expression}"

    def combine(self, other):
        # TODO: check description and initial value for consistency
        # print(self.variable.symbol, other.variable.symbol)
        # assert self.variable.symbol == other.variable.symbol
        # TODO: Check if we want to mutate this assignment, or rather produce a new one
        self.expression += other.expression


class ParameterAssignment(Assignment):
    def __init__(self, symbol_wrapper, expression):
        super().__init__(symbol_wrapper, expression)
        # We ensure we that the symbol_wrapper is instance of Parameter.
        if type(self.symbol_wrapper) is SymbolWrapper:
            self.symbol_wrapper = Parameter(
                self.symbol_wrapper.symbol,
                self.expression,
                self.symbol_wrapper.description,
            )

    # Parameters have this annoying data redundancy in that they also
    # store their own value. This is already in expression.
    # So we need to copy that over.
    def sync_param_value(self):
        self.parameter.value = self.expression

    def substitute_symbol(self, old_symbol, new_symbol):
        super().substitute_symbol(old_symbol, new_symbol)
        self.sync_param_value()

    # def substitute_parameter_assignments(self, parameter_assignments):
    #     super().substitute_parameter_assignments(parameter_assignments)
    #     self.sync_param_value()

    @property
    def parameter(self):
        return self.symbol_wrapper


class SymbolIdentification:
    """
    Identify two symbols as equal
    """

    def __init__(self, new_symbol, old_symbol):
        self.old_symbol = old_symbol
        self.new_symbol = new_symbol

    def __str__(self):
        return f"SymbolIdentification {self.new_symbol} = {self.old_symbol}"


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

    def __repr__(self):
        return f"{type(self).__name__} {self.name}"


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

    def __repr__(self):
        return f"{type(self).__name__} {self.name} with {self.assignment}"


class CompiledVariablePort(CompiledPort):
    pass


class CompiledOutputPort(CompiledPort):
    pass


class CompiledInputPort(CompiledPort):
    def __init__(self, port):
        assert isinstance(port, InputPort)
        super().__init__(port, None)
        self.default_value = port.default_value

    def substitute_symbol(self, old_symbol, new_symbol):
        assert isinstance(old_symbol, sym.Symbol)
        assert isinstance(new_symbol, sym.Symbol)
        assert isinstance(self.symbol, sym.Symbol)
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

    def __init__(
        self, name: str, assignments: List[Assignment] = [], expose_ports=True
    ):
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
                    self.input_ports[name] = InputPort(name)
                else:
                    raise ValueError(
                        f"Expression contains symbol {name} but there is no "
                        "corresponding input port."
                    )
        self.assignments[parameter_name] = assignment
        self.output_ports[parameter_name] = OutputPort(parameter_name)

    def compile(self, prefix_names=False, global_symbols=set()):
        compiled = CompiledPortedObject(self.name)
        for name, input_port in self.input_ports.items():
            compiled.input_ports[name] = CompiledInputPort(input_port)
        for name, output_port in self.output_ports.items():
            assignment = self.assignments[name]
            compiled.output_ports[name] = CompiledOutputPort(output_port, assignment)
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
            name: child.compile(prefix_names=True)
            for name, child in self.children.items()
        }

        # Compile own input ports. Not much happening for input ports.
        for name, input_port in self.input_ports.items():
            compiled.input_ports[name] = CompiledInputPort(input_port)

        # For each child input port, we have to ensure it's connected or has a default value

        unconnected_child_input_ports = {}
        unconnected_child_variable_ports = {}
        for child_name, child in compiled.children.items():
            # Collect all child input ports
            for name, port in child.input_ports.items():
                new_name = HIERARCHY_SEPARATOR.join([child_name, name])
                unconnected_child_input_ports[new_name] = port
            # Collect all child variable ports
            for name, port in child.variable_ports.items():
                new_name = HIERARCHY_SEPARATOR.join([child_name, name])
                unconnected_child_variable_ports[new_name] = port
            # Pass forward internal variable/parameter assignments
            compiled.internal_variable_assignments.update(
                child.internal_variable_assignments
            )
            compiled.internal_parameter_assignments.update(
                child.internal_parameter_assignments
            )
            # Pass forward assignments from output ports
            # TODO: Unconnected output ports are an indication that something may be wrong
            # If an output port is not connected, we could consider discarding it
            for name, port in child.output_ports.items():
                assg = port.assignment
                compiled.internal_parameter_assignments[assg.name] = assg

        # Process directed wires. In the process, we check which child input
        # ports don't have an incoming wire using unconnected_child_input_ports.
        for wire in self.directed_wires:
            if wire.destination_port in unconnected_child_input_ports:
                # Goes from own input or child output port to child input port.
                # In all of these cases, the ports have been pre-compiled
                source = compiled.get_port_by_name(wire.source_port)
                destination = compiled.get_port_by_name(wire.destination_port)
                assert type(destination) is CompiledInputPort
                # We're dropping the destination symbol in favor of the source
                assg = SymbolIdentification(source.symbol, destination.symbol)
                compiled.symbol_identifications.append(assg)
                unconnected_child_input_ports.pop(wire.destination_port)
            elif wire.destination_port in self.output_ports:
                source = compiled.get_port_by_name(wire.source_port)
                destination = self.get_port_by_name(wire.destination_port)
                assert type(destination) is OutputPort
                if self.is_own_port(wire.source_port):
                    # Goes from own input port to own output port.
                    assg_out = ParameterAssignment(destination.symbol, source.symbol)
                    compiled.output_ports[destination.name] = CompiledOutputPort(
                        destination, assg_out
                    )
                    # TODO: I don't see a use case for this
                    # Raising an error because I haven't tested the code above
                    raise ValueError(
                        "Why are you connecting an input port directly to an output port?"
                    )
                else:
                    # Goes from child output/variable port to own output port.
                    # We create a compiled output port
                    assg = ParameterAssignment(destination.symbol, source.symbol)
                    compiled.output_ports[destination.name] = CompiledOutputPort(
                        destination, assg
                    )
            else:
                raise WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    "DirectedWire destination should be output port "
                    f"or child input port but is {wire.destination_port}"
                )

        # Find unconnected child input ports and check for default values
        bad_input_ports = []
        for name, port in unconnected_child_input_ports.items():
            if port.default_value is None:
                bad_input_ports.append(name)
            else:
                # Initialize their parameters with initial values
                assg = ParameterAssignment(port.symbol, port.default_value)
                compiled.internal_parameter_assignments[name] = assg
        if bad_input_ports:
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                "The following child input ports are unconnected "
                f"and have no default value: {bad_input_ports}"
            )

        # Process variable aggregation wiring
        # TODO: Warn if there is a variable port that is not connected to children
        compiled.variable_ports = {}
        for wiring in self.variable_aggregation_wiring:
            # Collect child ports and their initial values
            child_ports = []
            initial_values = set()
            for port_name in wiring.child_ports:
                unconnected_child_variable_ports.pop(port_name)
                port = compiled.get_port_by_name(port_name)
                child_ports.append(port)
                initial_values.add(port.assignment.variable.initial_value)
            # Pass initial value forward to parent port
            initial_values -= {None}
            if len(initial_values) > 1:
                raise ValueError(
                    f"Inconsistent initial values for variable {wiring.parent_port}: {initial_values}."
                )
            elif initial_values:
                initial_value = initial_values.pop()
            else:
                initial_value = None

            if wiring.parent_port is not None:
                new_var = Variable(wiring.parent_port, initial_value)
            elif wiring.output_name is not None:
                new_var = Variable(wiring.output_name, initial_value)
            else:
                raise WiringError(
                    f"For VariableAggregationWiring, either parent_port "
                    "or output_name need to be provided"
                )
            # Combine RHSs of each child variable, and set child variables equal
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
                compiled.internal_variable_assignments[new_var.name] = assg

        # Make unconnected child ports into unexposed variables
        for name, port in unconnected_child_variable_ports.items():
            compiled.internal_variable_assignments[name] = port.assignment

        compiled.sub_symbol_identifications()

        # Align the dictionary keys with the names of the symbols
        # whose assignments the dictionary is storing.
        # This has to happen after all the wiring compilation,
        # because the wires refer to the child + port name within the child,
        # so the child name cannot be part of the dictionary key while
        # the wiring is compiled.
        compiled.remap_dict_keys()

        if prefix_names:
            # After this, all variables/parameters appearing everywhere
            # are prefixed by the name of the ported object.
            # This, however, does not apply to the dictionary keys,
            # see above for the reasoning
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
            self.sub_everywhere(
                symbol_identification.old_symbol, symbol_identification.new_symbol
            )

    def get_all_symbol_containers(self):
        return itertools.chain(
            self.input_ports.items(),
            self.output_ports.items(),
            self.variable_ports.items(),
            self.internal_variable_assignments.items(),
            self.internal_parameter_assignments.items(),
        )

    def sub_prefixed_symbols(self):
        """
        Replaces all non-global symbols by adding the compiled object's
        name as a prefix.

        This is done in both the LHS and RHS of the assignments, however,
        the dictionary keys are NOT affected.
        """
        for name, symbol_container in self.get_all_symbol_containers():
            assert name == symbol_container.name
            old_symbol = symbol_container.symbol
            new_symbol = sym.Symbol(HIERARCHY_SEPARATOR.join([self.name, name]))
            self.sub_everywhere(old_symbol, new_symbol)

    def remap_dict_keys(self):
        # Remap dictionary keys to add prefix
        for containers in [
            self.input_ports,
            self.output_ports,
            self.variable_ports,
            self.internal_variable_assignments,
            self.internal_parameter_assignments
        ]:
            re_keyed = {content.name : content for name, content in containers.items()}
            containers.clear()
            containers.update(re_keyed)

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
            assg_dict[str(assg.symbol)] = assg
        for name, port in self.input_ports.items():
            if name in assg_dict:
                self.internal_parameter_assignments[name] = assg_dict[name]
            elif port.default_value is not None:
                new_assg = ParameterAssignment(name, port.default_value)
                self.internal_parameter_assignments[name] = new_assg
            else:
                raise ValueError(f"Undefined input parameter: {name}")
        self.input_ports = {}

    def get_assignments(self):
        self.set_input_parameters()

        parameter_assignments = list(
            itertools.chain(
                (p.assignment for p in self.output_ports.values()),
                self.internal_parameter_assignments.values(),
            )
        )
        variable_assignments = list(
            itertools.chain(
                (p.assignment for p in self.variable_ports.values()),
                self.internal_variable_assignments.values(),
            )
        )

        return variable_assignments, parameter_assignments


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
