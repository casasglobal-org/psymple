from abc import ABC, abstractmethod

import warnings

from .assignments import (
    Assignment,
    DifferentialAssignment,
    ParameterAssignment,
)

from .errors import (
    ValidationError,
)

from .ports import (
    Port,
    InputPort,
    OutputPort,
    VariablePort,
)


class PortedObject(ABC):
    """
    Base class implementing ported objects. Cannot be instantiated directly.

    Methods:
        add_input_ports
        add_output_ports
        add_variable_ports
        parse_port_entry
    """

    def __init__(
        self,
        name: str,
        input_ports: list[InputPort | dict | tuple | str] = [],
        output_ports: list[OutputPort | dict | str] = [],
        variable_ports: list[VariablePort | dict | str] = [],
        parsing_locals: dict = {},
    ):
        """
        Construct a PortedObject.

        Args:
            name: a string which must be unique for each `PortedObject` inside a common
                [`CompositePortedObject`][psymple.build.CompositePortedObject].
            input_ports: list of input ports to expose. 
                See [add_input_ports][psymple.build.abstract.PortedObject.add_input_ports].
            output_ports: list of output ports to expose. 
                See [add_output_ports][psymple.build.abstract.PortedObject.add_input_ports].
            variable_ports: list of variable ports to expose. 
                See [add_variable_ports][psymple.build.abstract.PortedObject.add_variable_ports].
            parsing_locals: a dictionary mapping strings to `sympy` objects.
        """
        self.name = name
        # Ports exposed to the outside, indexed by their name
        self.variable_ports = {}
        self.input_ports = {}
        self.output_ports = {}
        
        self.parsing_locals = parsing_locals
        self.add_input_ports(*input_ports)
        self.add_output_ports(*output_ports)
        self.add_variable_ports(*variable_ports)

    def _check_existing_port_names(self, port: Port):
        """
        Checks if a port name is valid by checking it is not an already a defined port or
        a key in self.parsing_locals.

        Args:
            port: instance of Port

        Returns:
            bool: whether or not the port has a valid name
        """
        if port.name in self.variable_ports | self.output_ports | self.variable_ports:
            warnings.warn(
                f"Port with name '{port.name}' doubly defined in PortedObject '{self.name}'. Port "
                f"will not be created."
            )
            return False
        elif port.name in self.parsing_locals:
            warnings.warn(
                f"Attempted to create port with name '{port.name}', but this is already defined "
                f"in the parsing_locals dictionary {self.parsing_locals}. Port will not be created."
            )
            return False
        else:
            return True

    def parse_port_entry(
        self, port_info: Port | dict | tuple | str, port_type: Port
    ) -> Port:
        """
        Coerce user entry data from port_info into an instance of port_type.

        Args:
            port_info: data passed to add_input_ports, add_output_ports, add_variable_ports methods
            port_type: subclass of Port to be instantiated by coerced port_info data.

        Returns:
            port: instance of Port parametrised by coerced port_info data.

        Raises:
            ValidationError: if the data in port_info cannot be successfully coerced.
        """
        if isinstance(port_info, port_type):
            port = port_info
        elif isinstance(port_info, dict):
            if "name" in port_info.keys():
                port = port_type(**port_info)
            else:
                # TODO: Could check more things about dictionary structure.
                raise ValidationError(
                    f'The dictionary {port_info} must have a "name" entry.'
                )
        elif isinstance(port_info, tuple):
            name = port_info[0]
            if issubclass(port_type, InputPort):
                port = port_type(
                    name=name,
                    default_value=port_info[1] if len(port_info) >= 2 else None,
                    description=port_info[2] if len(port_info) >= 3 else "",
                )
            else:
                port = port_type(
                    name=name,
                    description=port_info[1] if len(port_info) >= 2 else "",
                )
        elif isinstance(port_info, str):
            port = port_type(name=port_info)
        else:
            raise ValidationError(
                f"The entry {port_info} does not have type {port_type}, dictionary or string"
            )
        return port

    def add_input_ports(self, *ports: InputPort | dict | tuple | str):
        """
        Add input ports to self.

        Args:
            *ports: data specifying an input port, in the form of:

                - an `InputPort` instance;
                - a dictionary specifying "name", and optionally "description" and "default_value";
                - a tuple, with the first entry specifying the name, and the second the default value;
                - a string, specifying the name of the port.

                Arguments can contain a mixture of the above data formats.

        Examples:
            Using an InputPort instance:
            >>> from psymple.ported_objects import VariablePortedObject, InputPort
            >>> X = VariablePortedObject(name="X")
            >>> X.add_input_ports(InputPort("A", default_value=6))
            >>> X._dump_input_ports()
            [{'name': 'A', 'description': '', 'default_value': 6}]

            Using a dictionary:
            >>> X = VariablePortedObject(name="X")
            >>> X.add_input_ports(dict(name = "A", description = "input port A", default_value=6))
            >>> X._dump_input_ports()
            [{'name': 'A', 'description': 'input port A', 'default_value': 6}]

            Using a tuple:
            >>> X = VariablePortedObject(name="X")
            >>> X.add_input_ports(("A", 6, "input port A"))
            >>> X._dump_input_ports()
            [{'name': 'A', 'description': 'input port A', 'default_value': 6}]

            Using a string (note that a description or default value cannot be specified):
            >>> X = VariablePortedObject(name="X")
            >>> X.add_input_ports("A")
            >>> X._dump_input_ports()
            [{'name': 'A', 'description': '', 'default_value': None}]

        """
        for port_info in ports:
            port = self.parse_port_entry(port_info, InputPort)
            self._add_input_port(port)

    def add_output_ports(self, *ports: OutputPort | dict | str):
        """
        Add input ports to self.

        Args:
            *ports: data specifying an output port, in the form of:

                - an `OutputPort` instance;
                - a dictionary specifying "name", and optionally "description";
                - a string, specifying the name of the port.

                Arguments can contain a mixture of the above data formats.

        Examples:
            Using an OutputPort instance:
            >>> from psymple.ported_objects import FunctionalPortedObject, OutputPort
            >>> X = FunctionalPortedObject(name="X")
            >>> X.add_output_ports(OutputPort("A", description="output port A"))
            >>> X._dump_output_ports()
            [{'name': 'A', 'description': 'output port A'}]

            Using a dictionary:
            >>> X = FunctionalPortedObject(name="X")
            >>> X.add_output_ports(dict(name = "A", description = "output port A"))
            >>> X._dump_output_ports()
            [{'name': 'A', 'description': 'output port A'}]

            Using a string (note that a description or default value cannot be specified):
            >>> X = FunctionalPortedObject(name="X")
            >>> X.add_output_ports("A")
            >>> X._dump_output_ports()
            [{'name': 'A', 'description': ''}]

        """
        for port_info in ports:
            port = self.parse_port_entry(port_info, OutputPort)
            self._add_output_port(port)

    def add_variable_ports(self, *ports: VariablePort | dict | str):
        """
        Add input ports to self.

        Args:
            *ports: data specifying a variable port, in the form of:

                - a `VariablePort` instance;
                - a dictionary specifying "name", and optionally "description";
                - a string, specifying the name of the port.

                Arguments can contain a mixture of the above data formats.

        Examples:
            Using an VariablePort instance:
            >>> from psymple.ported_objects import VariablePortedObject, VariablePort
            >>> X = VariablePortedObject(name="X")
            >>> X.add_variable_ports(VariablePort("A", description="variable port A"))
            >>> X._dump_variable_ports()
            [{'name': 'A', 'description': 'variable port A'}]

            Using a dictionary:
            >>> X = VariablePortedObject(name="X")
            >>> X.add_variable_ports(dict(name = "A", description = "variable port A"))
            >>> X._dump_variable_ports()
            [{'name': 'A', 'description': 'variable port A'}]

            Using a string (note that a description or default value cannot be specified):
            >>> X = VariablePortedObject(name="X")
            >>> X.add_variable_ports("A")
            >>> X._dump_variable_ports()
            [{'name': 'A', 'description': ''}]

        """
        for port_info in ports:
            port = self.parse_port_entry(port_info, VariablePort)
            self._add_variable_port(port)

    def _add_input_port(self, port: InputPort):
        if self._check_existing_port_names(port):
            self.input_ports[port.name] = port

    def _add_output_port(self, port: OutputPort):
        if self._check_existing_port_names(port):
            self.output_ports[port.name] = port

    def _add_variable_port(self, port: VariablePort):
        if self._check_existing_port_names(port):
            self.variable_ports[port.name] = port

    def _get_port_by_name(self, port: str):
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

    @abstractmethod
    def to_data(self):
        """
        Every subclass of PortedObject must implement a dismantler method to_data such that
        every instance X can be recreated by calling X.to_data().to_ported_object().
        """
        pass

    def _dump_input_ports(self):
        """
        Return the list of input port data of self.
        """
        input_ports = [port._to_data() for port in self.input_ports.values()]
        return input_ports

    def _dump_output_ports(self):
        """
        Return the list of output port data of self.
        """
        output_ports = [port._to_data() for port in self.output_ports.values()]
        return output_ports

    def _dump_variable_ports(self):
        """
        Return the list of variable port data of self.
        """
        variable_ports = [port._to_data() for port in self.variable_ports.values()]
        return variable_ports


class PortedObjectWithAssignments(PortedObject):
    """
    Abstract class to hold common functionality of VariablePortedObject and FunctionalPortedObject.
    Cannot be instantiated directly.
    """

    def __init__(
        self,
        name: str,
        input_ports: list = [],
        output_ports: list = [],
        variable_ports: list = [],
        parsing_locals: dict = {},
    ):
        super().__init__(
            name, input_ports, output_ports, variable_ports, parsing_locals
        )
        self.assignments = {}

    def parse_assignment_entry(
        self,
        assignment_info: Assignment | dict | tuple,
        assignment_type: Assignment,
    ) -> Assignment:
        """
        Coerce user entry data from assignment_info into an instance of assignment_type.

        Args:
            assignment_info: data specifying assignment formation
            assignment_type: subclass of Assignment to be instantiated by coerced assignment_info data.

        Returns:
            assignment: instance of Assignment parametrised by coerced assignment_info data.

        Raises:
            ValidationError: if the data in assignment_info cannot be successfully coerced.
        """
        if isinstance(assignment_info, assignment_type):
            return assignment_info
        elif isinstance(assignment_info, dict):
            keys = assignment_info.keys()
            if "expression" in keys:
                if issubclass(assignment_type, DifferentialAssignment):
                    if "variable" in keys:
                        assg = assignment_type(
                            assignment_info["variable"],
                            assignment_info["expression"],
                            self.parsing_locals,
                        )
                        return assg
                    else:
                        raise ValidationError(
                            f'The dictionary {assignment_info} must contain a key "variable" to define a differential assignment'
                        )
                if issubclass(assignment_type, ParameterAssignment):
                    if "parameter" in keys:
                        assg = assignment_type(
                            assignment_info["parameter"],
                            assignment_info["expression"],
                            self.parsing_locals,
                        )
                        return assg
                    else:
                        raise ValidationError(
                            f'The dictionary {assignment_info} must contain a key "parameter" to define a parameter assignment'
                        )
            else:
                raise ValidationError(
                    f'The dictionary {assignment_info} must contain a key "expression" to define an assignment'
                )
        elif isinstance(assignment_info, tuple):
            return assignment_type(
                assignment_info[0], assignment_info[1], self.parsing_locals
            )
        else:
            raise ValidationError(
                f"The entry {assignment_info} does not have type {assignment_type}, dictionary or tuple."
            )

    def _dump_assignments(self):
        if self.assignments:
            assignments = [assg._to_data() for assg in self.assignments.values()]
            return assignments
        else:
            return None
