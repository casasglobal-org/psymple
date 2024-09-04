import warnings
import json
import itertools

import sympy as sym

from sympy import (
    symbols,
)

from ..build import HIERARCHY_SEPARATOR

from .abstract import (
    PortedObject,
    PortedObjectWithAssignments,
)

from .assignments import (
    ParameterAssignment,
    DifferentialAssignment,
    FunctionalAssignment,
    DefaultParameterAssignment,
)

from .compiled_ports import (
    CompiledInputPort,
    CompiledOutputPort,
    CompiledVariablePort,
)

from .errors import (
    WiringError,
    ValidationError,
)

from .ports import (
    InputPort,
    OutputPort,
    VariablePort,
)

from .wires import (
    SymbolIdentification,
    VariableAggregationWiring,
    DirectedWire,
)

from psymple.abstract import DependencyError
from psymple.variables import (
    Parameter,
    Variable,
)


class RequiredInputParameter(Parameter):
    """
    A convenience class to identify parameters of a directly compiled object which did not
    have a default value specified. These are values which must be specified before simulation.
    """
    def __init__(self, symbol, description = ""):
        super().__init__(symbol, None, description)



class PortedObjectData(dict):
    """
    A dictionary holding the information defining a PortedObject instance.
    """
    def __init__(self, *, metadata: dict, object_data: dict):
        """
        Create a PortedObjectData instance.

        Args:
            metadata: dictionary storing ported object identifiers including `"name"`
                and `"type"`
            object_data: dictionary to be passed to ported object constructor
        """
        self._check_metadata(metadata)
        self._check_object_data(object_data)
        super().__init__(metadata=metadata, object_data=object_data)

    @classmethod
    def from_json(cls, file):
        data = json.loads(file)
        return cls(**data)

    def to_json(self):
        return json.dumps(self)

    def _check_metadata(self, data):
        # Checks that the format of metadata is parsable
        REQ_KEYS = {"type", "name"}
        if not REQ_KEYS <= data.keys():
            raise KeyError(f"Object metadata {data} must include keys {REQ_KEYS}")
        
    def _check_object_data(self, data):
        # Checks that the format of object_data is parsable
        ALLOWED_KEYS = {"assignments", "input_ports", "variable_ports", "output_ports", "variable_wires", "directed_wires", "children", "create_input_ports"}
        if extra_keys := data.keys() - ALLOWED_KEYS:
            raise KeyError(f"Object data {data} cannot include keys {extra_keys}")
        
    def to_ported_object(self, parsing_locals: dict = {}) -> PortedObject:
        """
        Builds a [`PortedObject`][psymple.build.abstract.PortedObject] instance from self. 
        The type of `PortedObject` is read from `self.type` and must be one of `"fpo"`, `"vpo"` or `"cpo"`. 

        Args:
            parsing_locals: a dictionary mapping strings to `sympy` objects.

        Returns:
            PortedObject: An instance of (or subclass of) `PortedObject` formed by
                passing `parsing_locals` and `**self.object_data` to the constructor indicated by
                `self.type`.
        """ 
        PORTED_OBJECT_TYPES = {
            "fpo": FunctionalPortedObject,
            "vpo": VariablePortedObject,
            "cpo": CompositePortedObject,
        }
        name = self.name
        type = self.type
        data = self.data
        ported_object = PORTED_OBJECT_TYPES[type]
        return ported_object(name=name, parsing_locals=parsing_locals, **data)

    @property
    def type(self) -> str:
        return self["metadata"]["type"]
    
    @property
    def name(self) -> str:
        return self["metadata"]["name"]
    
    @property
    def data(self) -> dict:
        return self["object_data"]



class VariablePortedObject(PortedObjectWithAssignments):
    """
    A ported object containing a collection of ODEs 
    ([`DifferentialAssignment`][psymple.build.assignments.DifferentialAssignment] instances).

    Each ODE is associated to a variable, which may or may not be exposed as a variable port.
    Symbols on the RHS of the ODE should be either:

    - Variables defined in this ported object
    - parameters that have corresponding input ports
    - globally defined symbols

    Methods:
        add_variable_assignments
        compile
    """

    def __init__(
        self,
        name: str,
        input_ports: list[InputPort | dict | tuple | str] = [],
        variable_ports: list[InputPort | dict | str] = [],
        assignments: list[DifferentialAssignment | dict | tuple] = [],
        create_input_ports: bool = True,
        parsing_locals: dict = {},
    ):
        """
        Construct a VariablePortedObject.

        Args:
            name: a string which must be unique for each `PortedObject` inside a common
                [`CompositePortedObject`][psymple.build.CompositePortedObject].
            input_ports: list of input ports to expose. 
                See [add_input_ports][psymple.build.abstract.PortedObject.add_input_ports].
            variable_ports: list of variable ports to expose. 
                See [add_variable_ports][psymple.build.abstract.PortedObject.add_variable_ports].
            assignments: list of differential assignments (ODEs). See 
                [add_variable_assignments][psymple.build.VariablePortedObject.add_variable_assignments]
            create_input_ports: if `True`, automatically expose all parameters as input ports. See Notes for more
                information.
            parsing_locals: a dictionary mapping strings to `sympy` objects.

        info: Notes
            - By default, each variable (dependent variable of each ODE) is automatically exposed as a
                variable port. Alternatively, chosen variables can be exposed by specifying
                them in the list variable_ports.

            - Parameters listed in input_ports are exposed and can be used in ODE expressions.

            - If `create_input_ports=True` (default), then each symbol appearing in an ODE which is not a
                variable or parameter defined in input_ports is also exposed as a parameter input port. The 
                created parameter will have no default value, and must be otherwise specified or linked by 
                a wire in a parent [`CompositePortedObject`][psymple.build.CompositePortedObject].
        """
        super().__init__(
            name,
            input_ports=input_ports,
            variable_ports=variable_ports,
            parsing_locals=parsing_locals,
        )
        # A dict of assignments indexed by the variable name
        self.internals = {}
        create_variable_ports = False if variable_ports else True
        self.add_variable_assignments(
            *assignments,
            create_variable_ports=create_variable_ports,
            create_input_ports=create_input_ports,
        )
        self.create_input_ports = create_input_ports

    def add_variable_assignments(
        self,
        *assignments: DifferentialAssignment | dict | tuple,
        create_variable_ports: bool = True,
        create_input_ports: bool = True,
    ):
        """
        Add variable assignments to self.

        Args:
            *assignments: data specifying a [`DifferentialAssignment`][psymple.build.assignments.DifferentialAssignment]. 
                Each entry must be:

                - an instance of `DifferentialAssignment`;
                - a `dict` with keys `"variable"` and `"expression"` which can be passed to
                    the `DifferentialAssignment` constructor
                - a `tuple`, whose first entry is passed to the `"variable"` argument and whose
                    second is passed to the `"expression"` argument of the `DifferentialAssignment`
                    constructor

            create_variable_ports: if `True`, variable ports exposing the variable of each assignment
                will automatically be created.
            create_input_ports: if `True`, input ports for each free symbol in the expression of each
                assignment will automatically be created.

        Raises:
            ValueError: if an assignment with the same variable name is already defined in self
        """
        for assignment_info in assignments:
            assignment = self.parse_assignment_entry(
                assignment_info, DifferentialAssignment
            )
            variable_name = assignment.symbol.name
            if variable_name in self.assignments:
                raise ValueError(
                    f"Variable '{variable_name}' in VariablePortedObject '{self.name}' doubly defined."
                )
            self.assignments[variable_name] = assignment
            if create_variable_ports:
                self.add_variable_ports(variable_name)
            elif variable_name not in self.variable_ports:
                self.internals[variable_name] = assignment.variable
        if create_input_ports:
            # Create input ports for all symbols that are not variables (exposed or internal) or already
            # specified as input ports.
            free_symbols = {
                symb.name
                for a in self.assignments.values()
                for symb in a.get_free_symbols()
            }
            internal_variables = set(self.internals.keys())
            variable_ports = set(self.variable_ports.keys())
            input_ports = set(self.input_ports.keys())
            undefined_ports = (
                free_symbols - internal_variables - variable_ports - input_ports
            )
            self.add_input_ports(*undefined_ports)

    def _assert_no_undefined_symbols(self, global_symbols=set()):
        """
        Called on compile, checking that all free symbols in all assignments are either

            - defined as a variable in an assignment
            - defined at an input port
            - are part of global_symbols

        Args:
            global_symbols: symbols to ignore in this check

        Raises:
            DependencyError: lists all symbols which are not accounted for.
        """
        variable_symbols = set()
        all_assignment_symbols = set()
        parameter_symbols = set()
        for name, port in self.input_ports.items():
            parameter_symbols.add(port.symbol)
        for assignment in self.assignments.values():
            variable_symbols.add(assignment.symbol)
            assignment_symbols = assignment.get_free_symbols()
            all_assignment_symbols |= assignment_symbols
        global_symbols = symbols(global_symbols)
        all_symbols = variable_symbols | parameter_symbols | global_symbols
        if not all_assignment_symbols.issubset(all_symbols):
            undefined_symbols = all_assignment_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in assignment of ported object {self.name}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}. Consider adding input ports for these."
            )

    def compile(self, prefix_names: bool = False, global_symbols: set = set()):
        """
        Generate a [`CompiledPortedObject`][psymple.build.ported_objects.CompiledPortedObject] with:

        - input ports generated from the input ports of self
        - variable ports exposing the variable and assignment of each assignment
            instance of self which have a corresponding variable port of self
        - internal variable assignments for each assignment instance of self
            which do not have a corresponding variable port of self

        Args:
            prefix_names: if `True`, all symbols in self will be prefixed with `self.name`
            global_symbols: symbols to pass to `_assert_no_undefined_symbols` method
        """
        self._assert_no_undefined_symbols(global_symbols | self.parsing_locals.keys())
        compiled = CompiledPortedObject(self.name, self.parsing_locals)
        for variable_name, assignment in self.assignments.items():
            if variable_name in self.variable_ports:
                compiled._add_variable_port(CompiledVariablePort(
                    self.variable_ports[variable_name], self.assignments[variable_name]
                    )
                )
            elif variable_name in self.internals:
                compiled.internal_variable_assignments[variable_name] = assignment

        for input_port in self.input_ports.values():
            compiled._add_input_port(CompiledInputPort(input_port))

        if prefix_names:
            compiled._sub_prefixed_symbols()
        return compiled
    
    def to_data(self) -> PortedObjectData:
        """
        A dismantler method such that every instance X of `VariablePortedObject`
        can be recreated by calling `X.to_data().to_ported_object()`

        Returns:
            data: a data object capturing the data of self
        """
        metadata = {
            "name": self.name,
            "type": "vpo",
        }
        object_data = {
            "input_ports": self._dump_input_ports(),
            "variable_ports": self._dump_variable_ports(),
            "assignments": self._dump_assignments(),
            "create_input_ports": self.create_input_ports,
        }
        return PortedObjectData(metadata=metadata, object_data=object_data)


class FunctionalPortedObject(PortedObjectWithAssignments):
    """
    A PortedObject containing a multivariate function.

    The function is defined by a set of 
    [`ParameterAssignment`][psymple.build.assignments.ParameterAssignment] instances.

    The function arguments are the free symbols on the RHS of the assignments,
    and should be exposed as input ports. The function values are the LHS of the
    assignments, and are automatically exposed as output ports.

    Function assignments whose expression references a parameter defined as
    the function value of another expression are not allowed.

    Methods:
        add_parameter_assignments
        compile
    """

    # TODO: Should undefined symbols be checked at compile rather than eagerly?

    def __init__(
        self,
        name: str,
        input_ports: list = [],
        assignments: list[ParameterAssignment | tuple | dict] = [],
        create_input_ports: bool = True,
        parsing_locals: dict = {},
    ):
        """
        Construct a FunctionalPortedObject.

        Args:
            name: a string which must be unique for each `PortedObject` inside a common
                [`CompositePortedObject`][psymple.build.CompositePortedObject].
            input_ports: list of input ports to expose. 
                See [add_input_ports][psymple.build.abstract.PortedObject.add_input_ports].
            assignments: list of functional assignments. See 
                [add_parameter_assignments][psymple.build.FunctionalPortedObject.add_parameter_assignments].
            create_input_ports: if `True`, automatically expose all parameters as input ports. See Notes for more
                information.
            parsing_locals: a dictionary mapping strings to `sympy` objects.

        info: Notes
            - The parameter of every created assignment is automatically exposed as an output port.

            - If `create_input_ports=True` (default), then each symbol appearing in a function which is not a
                parameter defined in input_ports is also exposed as a parameter input port. The 
                created parameter will have no default value, and must be otherwise specified or linked by 
                a wire in a parent [`CompositePortedObject`][psymple.build.CompositePortedObject].
        """
        # TODO: Functional ported objects should take lists of assignments to a list of output port
        super().__init__(name, input_ports=input_ports, parsing_locals=parsing_locals)
        self.add_parameter_assignments(*assignments, create_input_ports=create_input_ports)
        self.create_input_ports = create_input_ports

    def add_parameter_assignments(
        self,
        *assignments: list[ParameterAssignment | dict | tuple],
        create_input_ports: bool = True,
    ):
        """
        Add parameter assignments to self.

        Args:
            *assignments: data specifying a [`ParameterAssignment`][psymple.build.assignments.ParameterAssignment]. 
                Each entry must be:

                - an instance of `ParameterAssignment`;
                - a `dict` with keys `"parameter"` and `"expression"` which can be passed to
                    the `ParameterAssignment` constructor
                - a `tuple`, whose first entry is passed to the `"parameter"` argument and whose
                    second is passed to the `"expression"` argument of the `ParameterAssignment`
                    constructor

            create_input_ports: if `True`, input ports for each free symbol in the expression of each
                assignment will automatically be created.

        Raises:
            ValueError: if an assignment with the same variable name is already defined in self      
            ValueError: if an expression contains a symbol with no corresponding input port
        """
        for assignment_info in assignments:
            assignment = self.parse_assignment_entry(
                assignment_info, FunctionalAssignment
            )
            parameter_name = assignment.parameter.name
            if parameter_name in self.assignments:
                raise ValueError(
                    f"Variable '{parameter_name}' in FunctionalPortedObject '{self.name}' doubly defined."
                )
            free_symbols = assignment.get_free_symbols()
            for symbol in free_symbols:
                name = symbol.name
                if name not in self.input_ports:
                    if create_input_ports:
                        self.add_input_ports(name)
                    else:
                        raise ValueError(
                            f"Expression contains symbol {name} but there is no "
                            "corresponding input port."
                        )
            self.assignments[parameter_name] = assignment
            self.output_ports[parameter_name] = OutputPort(parameter_name)

    def compile(self, prefix_names: bool = False):
        """
        Generate a [`CompiledPortedObject`][psymple.build.ported_objects.CompiledPortedObject] with:

        - input ports generated from input ports of self
        - output ports exposing the parameter and assignment of each assignment
            instance of self

        Args:
            prefix_names: if `True`, all symbols in self will be prefixed with `self.name`
        """        
        compiled = CompiledPortedObject(self.name, self.parsing_locals)
        # Pass input ports of self through to input ports of compiled object
        for name, input_port in self.input_ports.items():
            compiled._add_input_port(CompiledInputPort(input_port))
        # Create an output port of compiled holding each assignment of self
        for name, output_port in self.output_ports.items():
            assignment = self.assignments[name]
            compiled._add_output_port(CompiledOutputPort(output_port, assignment))
        # Prefix names  for objects compiled as children
        if prefix_names:
            compiled._sub_prefixed_symbols()
        return compiled
    
    def to_data(self) -> PortedObjectData:
        """
        A dismantler method such that every instance X of `VariablePortedObject`
        can be recreated by calling `X.to_data().to_ported_object()`

        Returns:
            data: a data object capturing the data of self
        """
        metadata = {
            "name": self.name,
            "type": "fpo",
        }
        object_data = {
            "input_ports": self._dump_input_ports(),
            "assignments": self._dump_assignments(),
            "create_input_ports": self.create_input_ports,
        }
        return PortedObjectData(metadata=metadata, object_data=object_data)


class CompositePortedObject(PortedObject):
    """
    A ported object containing other ported object instances whose ports are connected by directed wires and
    variable wires.

    # Directed wires 

    Directed wires connect:

    - an input port of self to input ports of children, or,
    - an output port of a child to input ports of children and/or upto one output port of self, or,
    - a variable port of a child to input ports of children.

    These wires capture functional composition. In the following example, a  `CompositePortedObject` instance
    `X` contains [`FunctionalPortedObject`][psymple.build.FunctionalPortedObject] instances `A` and `B`. 
    Object `A` specifies the assignment \( x = f(y) \) and `B` specifies the assignment \( r = g(u,v) \). 
    Connecting output port `x` of `A` (accessed by `"A.x"`) to input port `u` of `B` (accessed by `"B.u"`) 
    with a directed wire represents the composite assignment \( r = g(f(y), v) \).

    Examples:
        >>> from psymple.build import FunctionalPortedObject, CompositePortedObject
        >>> A = FunctionalPortedObject(name="A", assignments=[("x", "f(y)")])
        >>> B = FunctionalPortedObject(name="B", assignments=[("y", "g(u,v)")])
        >>> X = CompositePortedObject(name="X", children=[A,B], directed_wires=[("A.x", "B.u")])
            
    See [`add_wires`][psymple.build.CompositePortedObject.add_wires] for the syntax to specify
    directed wires.

    # Variable wires

    Variable wires connect variable ports of children to upto one variable port of self.

    These wires capture ODE aggregation: 
    
    info: ODE aggregation 
        The *aggregation* of the ODEs \( dx/dt = f(x,t,a) \) and \( dy/dt = g(y,t,b) \), identifying
        \( (x,y) \longrightarrow z \), is the ODE \( dz/dt = f(z,t,a) + g(z,t,b) \). 
    
    In the following example, a  `CompositePortedObject` instance `X` contains 
    [`VariablePortedObject`][psymple.build.FunctionalPortedObject] instances `A` and `B`. Object
    `A` specifies the ODE \( dx/dt = f(x,t,a) \) and `B` specifies the ODE \( dy/dt = g(y,t,b) \). Aggregating
    variable port `x` of `A` (accessed by `"A.x"`) and variable port `y` of `B` (accessed by `"B.y"`) and 
    exposing at variable port `z` of `X` (identifying \( (x,y) \longrightarrow z \)) represents the
    ODE \( dz/dt = f(z,t,a) + g(z,t,b) \).
    
    Examples:
        >>> from psymple.build import FunctionalPortedObject, CompositePortedObject
        >>> A = FunctionalPortedObject(name="A", assignments=[("x", "f(x,t,a)")])
        >>> B = FunctionalPortedObject(name="B", assignments=[("y", "g(y,t,b)")])
        >>> X = CompositePortedObject(name="X", children=[A,B], variable_ports = ["z"], variable_wires=[(["A.x", "B.u"], "z")])      

    See [`add_wires`][psymple.build.CompositePortedObject.add_wires] for the syntax to specify
    directed wires.

    Methods:
        add_children
        add_wires
        add_directed_wire
        add_variable_wire
        compile

    warning: Requirements
        - Every input port of self should be the source of at least one directed wire
        
        - Every output port of self must be the destination of exactly one directed wire
        
        - Every variable port of self must be the destination of at most one variable wire

        - Every input port of a child must either have a default value or a 
            directed wire connected to it
        
        - Every output port of a child should have a directed wire going out of it
        
        - Every variable port of a child should have a variable wire connected to it

        - The directed wires should have no cycles (when contracting child ported 
            objects into nodes of a graph)
    """
    def __init__(
        self,
        name: str,
        children: list[PortedObject | PortedObjectData] = [],
        input_ports: list[InputPort | dict | tuple | str] = [],
        output_ports: list[OutputPort | dict | str] = [],
        variable_ports: list[VariablePort | dict | str] = [],
        variable_wires: list[dict | tuple] = [],
        directed_wires: list[dict | tuple] = [],
        parsing_locals: dict = {},
    ):
        """
        Construct a CompositePortedObject.

        Args:
            name: a string which must be unique for each `PortedObject` inside a common
                [`CompositePortedObject`][psymple.build.CompositePortedObject].
            children: list of children to add. 
                See [add_children][psymple.build.CompositePortedObject.add_children].
            input_ports: list of input ports to expose. 
                See [add_input_ports][psymple.build.abstract.PortedObject.add_input_ports].
            output_ports: list of output ports to expose. 
                See [add_output_ports][psymple.build.abstract.PortedObject.add_input_ports].
            variable_ports: list of variable ports to expose. 
                See [add_variable_ports][psymple.build.abstract.PortedObject.add_variable_ports].
            variable_wires: list of variable wires to create. See
                [add_wires][psymple.build.CompositePortedObject.add_wires].
            directed_wires: list of directed wires to create. See
                [add_wires][psymple.build.CompositePortedObject.add_wires].
            parsing_locals: a dictionary mapping strings to `sympy` objects.

        info: Note
            There is no automatic creation of ports in a `CompositePortedObject`
        """
        super().__init__(name, input_ports, output_ports, variable_ports, parsing_locals)
        self.children = {}
        self.variable_aggregation_wiring = []
        self.directed_wires = []
        self.add_children(*children)
        self.add_wires(variable_wires=variable_wires, directed_wires=directed_wires)

    def _is_own_port(self, name: str):
        return not (HIERARCHY_SEPARATOR in name)

    def add_children(self, *children: PortedObjectData | PortedObject):
        """
        Add children to `self`. A child is a `PortedObject` instance whose ports and assignments
        become available to `self`.

        Args:
            *children: instance of `PortedObject` or `PortedObjectData` specifying a
                ported object. Entries can be a mixture of types.
        """
        for data in children:
            # Attempt to coerce dictionary into PortedObjectData
            if isinstance(data, dict):
                if not type(data) == PortedObjectData:
                    data = PortedObjectData(**data)
                self._build_child(data)
            elif isinstance(data, PortedObject):
                self._add_child(data)

    def _build_child(self, child_data: PortedObjectData):
        # Build a ported object instance from data
        if not type(child_data) == PortedObjectData:
            raise TypeError(f"Argument 'child_data' must have type PortedObjectData, not {type(child_data)}")
        child = child_data.to_ported_object(parsing_locals=self.parsing_locals)
        self._add_child(child)

    def _add_child(self, child):
        if child.name in self.children:
            raise ValueError(f"Child {child.name} already exists in ported object {self.name}")
        self.children[child.name] = child

    def add_wires(self, variable_wires: list = [], directed_wires: list = []):
        """
        Add wires to self.

        Variable wires aggregate a set of child variable ports, and either

        - expose the result as a variable port of self, or,
        - store the result internally. 
        
        Either a parent port or internal name must be provided. Specifying a parent port will 
        override the internal name.
    
        Directed wires connect

        - an input port of self to input ports of children, or,
        - an output port of a child to input ports of children and/or upto one output port of self, or,
        - a variable port of a child to input ports of children.

        Args:
            variable_wires: a list of either:

                - a dictionary specifying `"child_ports"` (`list[str]`), and either `"parent_port"` (`str`),
                    or `"output_name"` (`str`);
                - a tuple which maps to the above dictionary, which must either be of the form
                    `(child_ports, parent_port)` or `(child_ports, None, output_name)`.

            directed_wires: a list of either:

                - a dictionary specifying `"source"` (`str`) and either `"destinations"` (`list[str]`)
                    or `"destination"` (`str`);
                - a tuple, which maps to the above dictionary, which must be of the form
                    `(source, destinations)` or `(source, destination)`.

        Raises:
            ValidationError: if the provided data cannot be parsed correctly.
        """
        for wire_info in variable_wires:
            if isinstance(wire_info, dict):
                keys = wire_info.keys()
                if "child_ports" in keys and (
                    "parent_port" in keys or "output_name" in keys
                ):
                    self.add_variable_wire(**wire_info)
                else:
                    raise ValidationError(
                        f"The dictionary {wire_info} must at least specify keys "
                        f'"child_ports" and either "parent_port" or "output_name.'
                    )
            elif isinstance(wire_info, tuple):
                self.add_variable_wire(
                    child_ports=wire_info[0],
                    parent_port=wire_info[1] if len(wire_info) >= 2 else None,
                    output_name=wire_info[2] if len(wire_info) == 3 else None,
                )
            else:
                raise ValidationError(
                    f"The information {wire_info} is not a dictionary or tuple"
                )

        for wire_info in directed_wires:
            if isinstance(wire_info, dict):
                keys = wire_info.keys()
                if keys == {"source", "destinations"} or keys == {
                    "source",
                    "destination",
                }:
                    self.add_directed_wire(*wire_info.values())
                else:
                    raise ValidationError(
                        f'The dictionary {wire_info} must contain keys "source" and either "destination" or "destinations".'
                    )
            elif isinstance(wire_info, tuple):
                self.add_directed_wire(*wire_info)
            else:
                raise ValidationError(
                    f"The element {wire_info} is not a dictionary or tuple"
                )

    def add_directed_wire(self, source_name: str, destination_names: str | list[str]):
        """
        Add a directed wire to self.

        Args:
            source_name: a string identifying the source port
            destination_names: a string or a list of strings identifying destination port(s)

        Raises:
            WiringError: if the provided ports cannot be found or are of incorrect type.

        info: Note
            It is recommended to use the [add_wires][psymple.build.CompositePortedObject.add_wires]
            method for additional entry options and to add multiple wires at the same time.
        """
        source_port = self._get_port_by_name(source_name)
        if source_port is None:
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. "
                f"Source port '{source_name}' does not exist."
            )
        if (
            source_name in self.output_ports
            or source_name in self.variable_ports
            or (source_name not in self.input_ports and type(source_port) is InputPort)
        ):
            # Source must be: own input, or child output, or child variable
            raise WiringError(
                f"Incorrect wiring in '{self.name}'. Source port '{source_name}' "
                "must be an input port or a child output/variable port."
            )
        # If a singular destination is specified, coerce it into a list
        if isinstance(destination_names, str):
            destination_names = [destination_names]
        for destination_name in destination_names:
            destination_port = self._get_port_by_name(destination_name)
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

        wire = DirectedWire(source_name, destination_names)
        self.directed_wires.append(wire)

    def add_variable_wire(
        self,
        child_ports: list[str],
        parent_port: str = None,
        output_name: str = None,
    ):
        """
        Add a variable wire to self.

        Args:
            child_ports: a list of strings identifying variable ports to aggregate 
            parent_port: a string identifying the parent variable port of self to identify with
            output_name: a string identifying the aggregation internally if a parent port 
                is not specified.

        Raises:
            WiringError: if the provided ports cannot be found or are of incorrect type.
 
        info: Note
            It is recommended to use the [add_wires][psymple.build.CompositePortedObject.add_wires]
            method for additional entry options and to add multiple wires at the same time.
        """
        if parent_port is not None:
            port = self._get_port_by_name(parent_port)
            if (
                port is None
                or not type(port) is VariablePort
                or not self._is_own_port(parent_port)
            ):
                WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    f"Parent port '{parent_port}' must be a variable port "
                    "of the ported object itself."
                )
        # Child ports should be ports of children
        for child_port in child_ports:
            port = self._get_port_by_name(child_port)
            if (
                port is None
                or not type(port) is VariablePort
                or self._is_own_port(child_port)
            ):
                WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    f"Child port '{child_port}' must be a variable port of a child."
                )
        wiring = VariableAggregationWiring(child_ports, parent_port, output_name)
        self.variable_aggregation_wiring.append(wiring)

    def _get_port_by_name(self, port_name: str):
        # Parses a string identifier to try to return a port of self or a child
        port = super()._get_port_by_name(port_name)
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
        return self.children[parent]._get_port_by_name(name)
    
    def _get_child(self, name: str):
        # Parses a string identifier to try to return a child ported object of self
        parts = name.split(HIERARCHY_SEPARATOR, 1)
        if len(parts) == 1:
            if name == self.name:
                return self
            elif name in self.children:
                return self.children[name]
            else:
                raise KeyError(f"{name} is not a child of {self.name}")
        else:
            parent_name, child_name = parts
            if parent_name == self.name:
                return self._get_child(child_name)
            elif parent_name in self.children:
                parent = self.children[parent_name]
                if (parent_type := type(parent)) == CompositePortedObject:
                    return parent._get_child(child_name)
                else:
                    raise TypeError(f"Ported object {parent_name} is of type {parent_type} and has no children.")
            else:
                raise KeyError(f"{name} is not a child of {self.name}")


    def compile(self, prefix_names: bool = False):
        """
        Generate a [`CompiledPortedObject`][psymple.build.ported_objects.CompiledPortedObject] with:

        - input ports generated from input ports of self
        - output ports generated from output ports of self, with assignments exposed by directed wires
        - variable ports generated from variable ports of self, with assignments exposed by variable wires
        - internal variable assignments generated from variable assignments of children not exposed to
            variable ports
        - internal parameter assignments generated from parameter assignments of children not exposed to
            output ports

        Args:
            prefix_names: if `True`, all symbols in self will be prefixed with `self.name`
        """       
        # Approch:
        #   - Compile each child of self recursively
        #   - Compile input ports of self
        #   - Collect input ports, variable ports and internal assignments of children
        #   - Process directed wires, producing compiled output ports, symbol identifications,
        #       or internal parameter assignments, as neccesary
        #   - Process variable wires, performing variable aggregations and producing compiled 
        #       variable ports or internal variable assignments, as necessary
        #   - Perform any symbol identifications
        #   - Perform consistency remapping and prefixing inside self, as necessary    
        compiled = CompiledPortedObject(self.name, self.parsing_locals)
        compiled.children = {
            name: child.compile(prefix_names=True)
            for name, child in self.children.items()
        }

        # Compile own input ports. Not much happening for input ports.
        for name, input_port in self.input_ports.items():
            #compiled.input_ports[name] = CompiledInputPort(input_port)
            compiled._add_input_port(CompiledInputPort(input_port))

        # For each child input port, we have to ensure it's
        # connected or has a default value

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
            # Pass forward internal variable/parameter assignments. Their keys are remapped
            # at this point to prevent duplication.
            compiled.internal_variable_assignments.update(
                {assg.name: assg for assg in child.internal_variable_assignments.values()}
            )
            compiled.internal_parameter_assignments.update(
                {assg.name: assg for assg in child.internal_parameter_assignments.values()}
            )
            # Pass forward assignments from output ports. Assignments may later be exposed
            # at an output port by a directed wire.
            # TODO: Unconnected output ports are an indication that something may be wrong
            # If an output port is not connected, we could consider discarding it
            for name, port in child.output_ports.items():
                if assg := port.assignment:
                    compiled.internal_parameter_assignments[assg.name] = assg

        # Process directed wires. We first determine the port which produces the wire symbol,
        # which depends on if the wire connects to output ports or not.
        for wire in self.directed_wires:

            # Directed wires connect:
            # - an input port to child input ports, or;
            # - a child output port to child input ports and at most one output port, or;
            # - a child variable port to child input ports.
            # We take cases on the number of output ports a directed wire connects to.
            outputs = [
                port for port in self.output_ports if port in wire.destination_ports
            ]
            num_outputs = len(outputs)
            if num_outputs > 1:
                # No wire can point to more than one output port
                raise WiringError(
                    f"Incorrect wiring in '{self.name}'. "
                    f"Directed wire from port {wire.source_port} "
                    "is connected to two different output ports. "
                )
            elif num_outputs == 1:
                # A wire ending at an output port can only start at a child output port.
                source = compiled._get_port_by_name(wire.source_port)
                if type(source) is CompiledOutputPort:
                    wire_root = self._get_port_by_name(outputs[0])
                else:
                    raise WiringError(
                        f"Incorrect wiring in '{self.name}'. "
                        "A DirectedWire pointing to an output port must start at "
                        f"a child OutputPort, not {wire.source_port} ."
                    )
            else:
                # The wire has only internal destinations.
                wire_root = compiled._get_port_by_name(wire.source_port)

            # Now we perform the identifications. In the process we check which child ports
            # don't have an incoming wire using unconnected_child_input_ports.
            for destination_port in wire.destination_ports:
                if destination_port in unconnected_child_input_ports:
                    # Goes from own input or child output port to child input port.
                    # In all of these cases, the ports have been pre-compiled
                    destination = compiled._get_port_by_name(destination_port)
                    assert type(destination) is CompiledInputPort
                    # Substitute the destination symbol for the wire symbol
                    symb_id = SymbolIdentification(wire_root.symbol, destination.symbol)
                    compiled.symbol_identifications.append(symb_id)
                    unconnected_child_input_ports.pop(destination_port)
                elif destination_port in self.output_ports:
                    # We can only be in this case if the source is a child output port,
                    # which has already been compiled
                    source = compiled._get_port_by_name(wire.source_port)
                    destination = self._get_port_by_name(destination_port)
                    assert type(destination) is OutputPort
                    # Substitute the source symbol for the output port symbol
                    symb_id = SymbolIdentification(wire_root.symbol, source.symbol)
                    compiled.symbol_identifications.append(symb_id)
                    # Pass forward the assignment at source, currently stored as an
                    # internal parameter assignment, to the output port.
                    source_assg = compiled.internal_parameter_assignments.pop(
                        source.name
                    )
                    #compiled.output_ports[destination.name] = CompiledOutputPort(
                    #    destination,
                    #    source_assg,
                    #)
                    compiled._add_output_port(CompiledOutputPort(
                        destination,
                        source_assg,
                    ))
                else:
                    raise WiringError(
                        f"Incorrect wiring in '{self.name}'. "
                        "DirectedWire destination should be output port "
                        f"or child input port but is {destination_port}"
                    )

        # Find unconnected child input ports and check for default values
        bad_input_ports = []
        for name, port in unconnected_child_input_ports.items():
            if port.default_value is None:
                bad_input_ports.append(name)
            else:
                # Initialize their parameters with default values
                assg = DefaultParameterAssignment(port.symbol, port.default_value, self.parsing_locals)
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
            # Collect child ports 
            child_ports = []
            for port_name in wiring.child_ports:
                unconnected_child_variable_ports.pop(port_name)
                port = compiled._get_port_by_name(port_name)
                child_ports.append(port)

            if wiring.parent_port is not None:
                new_var_name = wiring.parent_port
            elif wiring.output_name is not None:
                new_var_name = wiring.output_name
            else:
                raise WiringError(
                    f"For VariableAggregationWiring, either parent_port "
                    "or output_name need to be provided"
                )
            # Combine RHSs of each child variable, and set child variables equal
            assg = DifferentialAssignment(new_var_name, "0")
            for child in child_ports:
                assg.combine(child.assignment)
                assert isinstance(child.assignment.symbol, sym.Symbol)
                compiled.symbol_identifications.append(
                    SymbolIdentification(assg.symbol, child.assignment.symbol)
                )
            if wiring.parent_port is not None:
                parent = self._get_port_by_name(wiring.parent_port)
                new_port = CompiledVariablePort(parent, assg)
                compiled._add_variable_port(new_port)
                #compiled.variable_ports[parent.name] = new_port
            else:
                compiled.internal_variable_assignments[new_var_name] = assg

        # Make unconnected child ports into unexposed variables
        for name, port in unconnected_child_variable_ports.items():
            compiled.internal_variable_assignments[name] = port.assignment

        compiled._sub_symbol_identifications()

        # Align the dictionary keys with the names of the symbols
        # whose assignments the dictionary is storing.
        # This has to happen after all the wiring compilation,
        # because the wires refer to the child + port name within the child,
        # so the child name cannot be part of the dictionary key while
        # the wiring is compiled. For internal assignments pulled up from
        # children, this remapping has already happened and those dictionaries
        # are unaffected.
        compiled._remap_dict_keys()

        if prefix_names:
            # After this, all variables/parameters appearing everywhere
            # are prefixed by the name of the ported object.
            # This, however, does not apply to the dictionary keys,
            # see above for the reasoning
            compiled._sub_prefixed_symbols()

        return compiled
    
    def _dump_children(self):
        data = [
            child.to_data() for child in self.children.values()
        ]
        return data
    
    def _dump_variable_wires(self):
        variable_wires = [
            wire._to_data() for wire in self.variable_aggregation_wiring
        ]
        return variable_wires

    def _dump_directed_wires(self):
        directed_wires = [
            wire._to_data() for wire in self.directed_wires
        ]
        return directed_wires
    
    def to_data(self) -> PortedObjectData:
        """
        A dismantler method such that every instance X of `CompositePortedObject`
        can be recreated by calling `X.to_data().to_ported_object()`

        Returns:
            data: a data object capturing the data of self
        """
        metadata = {
            "name": self.name,
            "type": "cpo",
        }
        object_data = {
            "children": self._dump_children(),
            "input_ports": self._dump_input_ports(),
            "output_ports": self._dump_output_ports(),
            "variable_ports": self._dump_variable_ports(),
            "directed_wires": self._dump_directed_wires(),
            "variable_wires": self._dump_variable_wires(),
        }
        return PortedObjectData(metadata=metadata, object_data=object_data)

class CompiledPortedObject(CompositePortedObject):
    """
    A ported object with compiled ports store exposable assignments, together 
    with internal assignments.

    warning: Note:
        This class should not be instantiated on its own. It is formed from the `compile` methods
        of 1PortedObject1 subclasses. 
    """
    def __init__(self, name: str, parsing_locals: dict = {}):
        """
        Instantiate a CompiledPortedObject.

        Args:
            name: a string which must be unique for each `PortedObject` inside a common
                [`CompositePortedObject`][psymple.build.CompositePortedObject].
            parsing_locals: a dictionary mapping strings to `sympy` objects.
        """
        super().__init__(name, parsing_locals=parsing_locals)
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
        # Inputs of self which must be provided before simulation
        self.required_inputs = {}
        # Equivalent symbols
        self.symbol_identifications = []

    def get_required_inputs(self) -> set[RequiredInputParameter]:
        """
        Returns the input parameters of `self` which do not have a default value.
        """
        return list(self.required_inputs.values())

    def get_assignments(self) -> tuple[list[DifferentialAssignment], list[ParameterAssignment]]:
        """
        Returns all assignments of self.

        - The first return value is all assignments at variable ports and all 
            internal variable assignments,
        - The second return value is all assignments at output ports and all
            internal parameter assignments.
        """
        self._set_input_parameters()

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

    def _sub_symbol_identifications(self):
        # Substitute equivalent symbols by a representative
        # TODO: Cycle detection
        for symbol_identification in self.symbol_identifications:
            self._sub_everywhere(
                symbol_identification.old_symbol, symbol_identification.new_symbol
            )

    def _add_input_port(self, port: CompiledInputPort):
        if self._check_existing_port_names(port):
            self.input_ports[port.name] = port

    def _add_output_port(self, port: CompiledOutputPort):
        if self._check_existing_port_names(port):
            self.output_ports[port.name] = port

    def _add_variable_port(self, port: CompiledVariablePort):
        if self._check_existing_port_names(port):
            self.variable_ports[port.name] = port

    def _get_all_symbol_containers(self):
        return itertools.chain(
            self.input_ports.items(),
            self.output_ports.items(),
            self.variable_ports.items(),
            self.internal_variable_assignments.items(),
            self.internal_parameter_assignments.items(),
        )

    def _sub_prefixed_symbols(self):
        """
        Replaces all non-global symbols by adding the compiled object's
        name as a prefix.

        This is done in both the LHS and RHS of the assignments, however,
        the dictionary keys are NOT affected.
        """
        for name, symbol_container in self._get_all_symbol_containers():
            assert name == symbol_container.name
            old_symbol = symbol_container.symbol
            new_symbol = sym.Symbol(HIERARCHY_SEPARATOR.join([self.name, name]))
            self._sub_everywhere(old_symbol, new_symbol)

    def _remap_dict_keys(self):
        # Remap dictionary keys to add prefix
        for containers in [
            self.input_ports,
            self.output_ports,
            self.variable_ports,
            self.internal_variable_assignments,
            self.internal_parameter_assignments,
        ]:
            re_keyed = {content.name: content for name, content in containers.items()}
            containers.clear()
            containers.update(re_keyed)

    def _sub_everywhere(self, old_symbol, new_symbol):
        assert isinstance(old_symbol, sym.Symbol)
        assert isinstance(new_symbol, sym.Symbol)
        for name, symbol_container in self._get_all_symbol_containers():
            symbol_container.substitute_symbol(old_symbol, new_symbol)

    def _set_input_parameters(self):
        for name, port in self.input_ports.items():
            if port.default_value is not None:
                new_assg = DefaultParameterAssignment(name, port.default_value, self.parsing_locals)
                self.internal_parameter_assignments[name] = new_assg
            else:
                req_input = RequiredInputParameter(name)
                self.required_inputs[name] = req_input