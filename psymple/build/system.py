from inspect import signature
from typing import Callable

import warnings

import matplotlib.pyplot as plt
import networkx as nx

from sympy import (
    Function,
    Number,
    Symbol,
    lambdify,
    symbols,
    parse_expr,
)

from psymple.build.errors import SystemError

from psymple.variables import (
    # Parameter,
    UpdateRule,
    SimParameter,
    SimUpdateRule,
    SimVariable,
    Variable,
    Container,
)

from psymple.build import (
    PortedObjectData,
    HIERARCHY_SEPARATOR,
)

from psymple.build.ported_objects import PortedObject

from psymple.build.assignments import (
    ParameterAssignment,
    DifferentialAssignment,
    FunctionalAssignment,
    DefaultParameterAssignment,
)

from psymple.simulate import Simulation

from psymple.simulate.simulation import SetterObject

#from psymple.io.create_system import System_Creator


class SystemData(dict):
    def __init__(self, *, metadata, ported_object):
        super().__init__(metadata=metadata, ported_object=ported_object)

class FunctionHandler:
    """
    Base class handing the creation and storage of system-wide utility functions and parameters.

    Methods:
        add_system_parameter
        add_utility_function
    """
    def add_system_parameter(
        self, name: str, function: Callable | str | int | float, signature: tuple = None
    ):
        """
        A system parameter is a system-wide function which, if not constant, may only depend on the independent 
        system variable `time` or existing system parameters.

        Args:
            name: the string identifier of the system parameter.
            function: a callable function or a string representation of its output.
            signature: the function signature. See `Notes` below for more details.

        Raises:
            TypeError: if the input `function` is not of a parsable type.

        Notes:
            If function is callable, the signature should be provided if the function arguments names are not system
            parameters or time. The following are acceptable calls:

            ```
            >>> system.add_system_parameter("T_avg", lambda T_min, T_max: (T_min + T_max)/2)
            >>> system.add_system_parameter("T_avg", lambda a, b: (a+b)/2, signature=("T_min", "T_max"))
            ```

            While the following call will fail because `"a"` and `"b"` are not recognised as system parameters.
            ```
            >>> system.add_system_paramter("T_avg", lambda a, b: (a+b)/2)
            ```

            If the function is symbolic, a signature only needs to be provided to control the display order of the
            function arguments. If not provided, the generation of the signature does not preserve the order in
            which the symbols appear. This does not affect the computation of the system parameter. For example,

            ```
            >>> system.add_system_parameter("T_ratio", "T_max / T_min")
            ```

            will always compute `T_ratio = T_max / T_min`, but may display as `T_ratio (T_max, T_min)` or
            `T_ratio (T_min, T_max)`.

            The provided signature must be a list or tuple containing exactly the symbols in the expression in the
            required order, for example:

            ```
            >>> system.add_system_parameter("T_ratio", "T_max / T_min", ("T_max", "T_min"))
            ```

            Then whenever `T_ratio` is written in an assignment definition, it will be interpreted and displayed
            as the function `T_ratio(T_max, T_min)`.
        """
        if name in self.system_parameters:
            warnings.warn(
                f"The system parameter {name} has already been defined. It will be overwritten."
            )
        if callable(function):
            args, nargs = self._inspect_signature(function)
            if signature:
                if signature != args:
                    if len(signature) not in nargs:
                        raise ValueError(
                            f"Signature validation failed. The provided signature {signature}"
                            f"is not a length accepted by the provided function: {nargs}."
                        )
            else:
                signature = args
            self._check_are_system_parameters(*signature)
            sym_func = self._add_callable_function(name, function, nargs=nargs)
        elif isinstance(function, (str, int, float)):
            function = str(function)
            sym_signature = self._generate_signature(function)
            if signature:
                assert all([isinstance(s, str) for s in signature])
                assert set(signature) == set(sym_signature)
            else:
                warnings.warn(
                    f"A signature for function {name} was not provided. The appearance of "
                    f"the function in displayed expressions may not be as expected."
                )
                signature = sym_signature
            self._check_are_system_parameters(*signature)
            sym_func = self._add_symbolic_function(name, function, signature)
        else:
            raise TypeError(f"Function {function} of type {type(function)} cannot be parsed.")
        # The signature needs to take into account sub-dependencies of existing system parameters
        sig = tuple(parse_expr(s, local_dict=self.system_parameters) for s in signature)
        if sig:
            self.system_parameters.update({name: sym_func(*sig)})
        else:
            self.system_parameters.update({name: sym_func()})

    def add_utility_function(self, name: str, function: Callable | str, signature: tuple = None):
        """
        A utility function is a system-wide function which can depend on any further created variable or parameter.
        They expand functions available to the user when defining assignments.

        Args:
            name: the string identifier of the system parameter.
            function: a callable function or a string representation of its output.
            signature: the function signature. See `Notes` below for more details.

        Raises:
            TypeError: if the input `function` is not of a parsable type.

        Notes:
            If function is callable, its signature will be inspected to determine the range of acceptable number of
            inputs. This is used to validate function entry in the creation of assignments.

            ```
            >>> from numpy import sin
            >>> system.add_utility_function("new_sin": sin)
            ```

            Entering `new_sin(a,b)` in an assignment will raise an exception because `numpy.sin` accepts exactly one
            argument. A signature can be provided to restrict the number of inputs of a function. _This is currently
            **not** recommended, and no signature argument should be provided_.

            If function is symbolic, a signature should be provided if the order of function arguments matters.
            If not provided, the function may not behave as expected. The provided signature must be a list or
            tuple containing exactly the symbols in the expression in the required order. For example,

            ```
            >>> system.add_utility_function("exp", "a**b")
            ```

            may evaluate as `exp(x,y) = x**y` or `exp(x,y) = y**x`. While,

            ```
            >>> system.add_utility_function("exp", "a**b", ("a", "b"))
            ```

            will always evaluate as `exp(x,y) = x**y`.
        """
        if name in self.utility_functions:
            warnings.warn(
                f"The utility function {name} has already been defined. It will be overwritten."
            )
        if callable(function):
            _, nargs = self._inspect_signature(function)
            if signature:
                assert set(signature).issubset(set(nargs))
                nargs = signature
            sym_func = self._add_callable_function(name, function, nargs=nargs)
        elif isinstance(function, str):
            sym_signature = self._generate_signature(function)
            if signature:
                assert set(signature) == set(sym_signature)
            else:
                warnings.warn(
                    f"A signature for function {name} was not provided. The behaviour of "
                    "the function may not be as expected."
                )
                signature = sym_signature
            sym_func = self._add_symbolic_function(name, function, signature)
        else:
            raise TypeError(f"Function {function} of type {type(function)} cannot be parsed.")
        self.utility_functions.update({name: sym_func})

    def _add_function(self, type, *data):
        """
        Parser called by `__init__` method if system parameters or utility functions are passed
        on instantiation.
        """
        for function_data in data:
            if isinstance(function_data, dict):
                pass
            elif isinstance(function_data, tuple):
                function_data = {
                    "name": function_data[0],
                    "function": function_data[1],
                    "signature": function_data[2] if len(function_data) == 3 else None,
                }
            else:
                raise SystemError(
                    f"Function creation data {function_data} must be of type "
                    f"tuple or dict."
                )
            if type == "system_parameter":
                self.add_system_parameter(**function_data)
            elif type == "utility_function":
                self.add_utility_function(**function_data)

    def _add_callable_function(self, name: str, callable, nargs: tuple = None):
        """
        Add a system-wide callable function.

        Name must be a string.

        The function will remain in symbolic form until simulation.
        """
        self._add_to_lambdify_ns(name, callable)
        if nargs == (0,):
            sym_func = Symbol(f"{name}")
        else:
            sym_func = Function(f"{name}", nargs=nargs)
        return sym_func

    def _inspect_signature(self, callable):
        """
        Returns the argument names and range of acceptable input lengths of a callable function.
        """
        sig = signature(callable)
        params = sig.parameters.values()
        pos_only = sum(1 for x in params if x.kind == x.POSITIONAL_ONLY)
        kw_only = sum(1 for x in params if x.kind == x.KEYWORD_ONLY)
        pos_or_kw = sum(1 for x in params if x.kind == x.POSITIONAL_OR_KEYWORD)
        if kw_only > 0:
            raise NotImplementedError(
                "Keyword only arguments have not been implemented yet"
            )
        elif pos_only > 0:
            min_nargs = pos_only
            max_nargs = pos_only + pos_or_kw
            nargs = tuple(range(min_nargs, max_nargs + 1))
        else:
            nargs = (pos_or_kw,)

        args = [x.name for x in params]

        return args, nargs

    def _generate_signature(self, expression: str):
        """
        Returns the names of free symbols in an expression.
        """
        expression = parse_expr(expression)
        signature = expression.free_symbols
        return tuple(symbol.name for symbol in signature)

    def _check_are_system_parameters(self, *params):
        """
        Checks if any of the provided strings in `params` are already defined
        as the system time symbol or in system params.

        Currently raises an exception.
        """
        time_name = self.time.symbol.name
        system_params = self.system_parameters.keys() | time_name
        not_system_params = set(params) - system_params
        if not_system_params:
            raise SystemError(
                f"The arguments {not_system_params} are not system parameters or "
                f"the time variable {time_name}."
            )

    def _add_to_lambdify_ns(self, name, callable):
        """
        `lambdify_ns` stores *a list of dict* objects, so it is harder to inspect. This function
        checks if an item with the given name is defined in `lambdify_ns`, and raises an exception
        if so. If not, `{name: callable}` is added *to the start* of `lambdify_ns`, since we need 
        functions to be processed in reverse order of how they are added.
        """
        entry = next(
            (
                entry
                for entry in self.lambdify_ns
                if (isinstance(entry, dict) and name in entry)
            ),
            None,
        )
        if entry:
            if name in self.system_parameters:
                what = "system parameter"
            elif name in self.utility_functions:
                what = "utility function"
            # Raising an exception instead of a warning at this point since this seems more serious
            raise SystemError(
                f"{name} has already been defined as a {what}. Use a different name."
            )
        self.lambdify_ns.insert(0, {name: callable})

    def _add_symbolic_function(
        self, name: str, expression=None, signature: list | tuple = None
    ):
        """
        Add a system-wide symbolic function.

        Name must be a string.

        The function will remain in symbolic form until simulation.
        """
        signature = symbols(signature)
        callable = lambdify(signature, expression, modules=self.lambdify_ns)

        self._add_to_lambdify_ns(name, callable)

        if signature:
            sym_func = Function(f"{name}", nargs=(len(signature),))
        else:
            sym_func = Function(f"{name}", nargs=(0,))
        return sym_func


class System(FunctionHandler, SetterObject):
    """
    A `System` is a three-way interface between:

    1. A [`PortedObject`][psymple.build.abstract.PortedObject] instance
        defining a model;
    2. Collections of data providing context to symbols and functions of
        [`Assignment`][psymple.abstract.Assignment] instances attached to
        the `PortedObject` instance. The three main data sources are:

        - time: the independent system variable which is simulated over;
        - utility functions: which provide a system-wide definition of
            a function call, and;
        - system parameters: which provide a system-wide definition of
            a symbol;

    3. A [`Simulation`][psymple.simulate.Simulation] instance which allows
        a model defined by the `PortedObject` instance to be simulated.

    Methods:
        add_system_parameter
        add_utility_function
        compile
        compute_parameter_update_order
        set_object
        set_parameters
        create_simulation
        get_readable_symbols
        get_readout
        to_data
    """

    def __init__(
        self,
        ported_object: PortedObject | PortedObjectData = None,
        utility_functions: list[dict | tuple] = [],
        system_parameters: list[dict | tuple] = [],
        time_symbol: str = "T",
        compile: bool = False,
    ):
        """
        Create a System instance.

        Args:
            ported_object: instance of `PortedObject` or `PortedObjectData defining the system model.
            utility_functions: list of the utility functions available in the system. See documentation
                for [`add_utility_function`][psymple.build.System.add_utility_function] for acceptable values.
            system_parameters: list of the system parameters available in the system. See documentation
                for [`add_system_paramter`][psymple.build.System.add_system_parameter] for acceptable values.
            time_symbol: The symbol used for the independent variable time in the system.
            compile: If `True` and `ported_object` is provided, then system will be compiled automatically.

        warning: Warning
            Overriding the time_symbol from `"T"` is not currently supported.
        """
        self.lambdify_ns = ["numpy", "scipy"]
        self.system_parameters = {}
        self.utility_functions = {}
        self.compiled = False
        self.simulations = {}
        self.ported_object = None

        if time_symbol != "T":
            warnings.warn(
                f"time symbol {time_symbol} has not been tested. Reverting back to T."
            )
            time_symbol = "T"
        self._create_time_variable(time_symbol)

        self._add_function("utility_function", *utility_functions)
        self._add_function("system_parameter", *system_parameters)

        if ported_object:
            self.set_object(ported_object, compile=compile)

    def set_object(
        self, ported_object: PortedObject | PortedObjectData, compile: bool = True
    ):
        """
        Set the ported object in the system. This will override any ported object currently
        set in the system.

        Args:
            ported_object: instance of `PortedObject` or `PortedObjectData` defining the system model.
            compile: if `True`, [`compile`][psymple.build.System.compile] will be called automatically.
        """
        self.ported_object = self._process_ported_object(ported_object)
        self.compiled = False
        # Variables and parameters need to be reset for a new object
        self._reset_variables_parameters()
        if compile:
            self.compile()

    def compile(self, child: str = None):
        """
        Compile the system at the specified ported object. This will compile the specified ported object,
        and then create the necessary variables and parameters for simulation.

        Args:
            child: a string identifying a child ported object from `self.ported_object`. If not provided,
                `self.ported_object` will be used.
        """
        self.simulations = {}
        self.required_inputs = []

        if not self.ported_object:
            raise SystemError(
                "No ported object specified in system. Use set_object() to set one first."
            )
        
        ported_object = self._build_ported_object()

        if child:
            ported_object = ported_object._get_child(child)

        compiled = ported_object.compile()

        variable_assignments, parameter_assignments = compiled.get_assignments()
        # self.sub_system_parameters(variable_assignments, parameter_assignments)

        required_inputs = compiled.get_required_inputs()

        self._reset_variables_parameters()

        variables, parameters = self._get_symbols(
            variable_assignments, parameter_assignments, required_inputs
        )

        self._create_simulation_variables(
            variable_assignments, variables | {self.time.symbol}, parameters
        )
        self._create_simulation_parameters(
            parameter_assignments, variables | {self.time.symbol}, parameters
        )
        self._create_input_parameters(required_inputs)
        self.compiled = True

    def set_parameters(self, parameter_values: dict[str, str | int | float] = {}):
        """
        Set input parameters at the system level. System must first have an associated ported object and
        must be compiled.

        Parameters which can be set or overridden:

        - any parameter from an input port of the system object, whether it has a default value or not,
        - any parameter from an input port of a nested child of the system object (these must already
            have been given a default value, but this can be overridden here).

        Parameter values must be constant, or functions of system variable `time` and/or existing system 
        parameters.

        Args:
            parameter_values: a dictionary of `parameter: value` pairs, where `parameter` is the string
                identifier of a parameter (an entry from `self.parameters`) and `value` is the value
                or function to assign.

        Raises:
            TypeError: if a value which is not of type `str`, `int`, `float` is entered.
            ParsingError: if the value expression contains forbidden symbols.
            TypeError: if the parameter is fixed and cannot be updated.
        """
        if not self.compiled:
            raise SystemError(f"System has not been compiled.")
        super().set_parameters(parameter_values)

    def set_initial_values(self, values: dict[str, int | float]):
        """
        Set initial values at the system level. System must first have an associated ported object and
        must be compiled.

        Initial values must be `int` or `float` instances only.

        Args:
            values: a dictionary of `variable: value` pairs where `variable` is the string
                identifier of a variable in `self.variables` and `value` is `int` or `float`.
        """
        if not self.compiled:
            raise SystemError(f"System has not been compiled.")
        super().set_initial_values(values)

    def _process_ported_object(self, ported_object):
        """
        Coerces a ported object into `PortedObjectData` format.
        """
        if isinstance(ported_object, PortedObject):
            ported_object = ported_object.to_data()
        if isinstance(ported_object, PortedObjectData):
            return ported_object
        else:
            raise TypeError(
                f"Ported object must be of type PortedObject or PortedObjectData, not {type(ported_object)}."
            )

    def _build_ported_object(self):
        """
        Builds a ported object in the system context, where expressions are interpreted
        using `self.system_parameters` and `self.utility_functions`. 
        """
        parsing_locals = self.system_parameters | self.utility_functions
        ported_object = self.ported_object.to_ported_object(parsing_locals)
        return ported_object

    """
    def sub_system_parameters(self, variable_assignments, parameter_assignments):
        for assg in variable_assignments + parameter_assignments:
            print("expr",assg.expression)
            print("system params",self.system_parameters)
            assg.expression = assg.expression.subs(self.system_parameters)
    """

    def _create_time_variable(self, time_symbol):
        # At the moment the only global variable is time
        time_symbol = Symbol(time_symbol)
        self.time = SimVariable(Variable(time_symbol, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                expression="1",
                variables={},
                parameters={},
                description="system time",
            )
        )

    def _check_required_parameters(self):
        return {
            parameter.name
            for parameter in self.parameters.values()
            if parameter.type == "required"
        }

    def create_simulation(
        self,
        name: str = None,
        solver: str = "continuous",
        initial_values: dict = {},
        input_parameters: dict = {},
    ) -> Simulation:
        """
        Create a Simulation instance from the system. 

        Args:
            name: if provided, the simulation will be stored in `self.simulations[name]`.
            solver: solver method to use.
            initial_values: a dictionary of `variable: value` pairs where `variable` is the string
                identifier of a variable in `self.variables` and `value` is `int` or `float`.
            input_parameters: a dictionary of `parameter: value` pairs, where `parameter` is the string
                identifier of a parameter (an entry from `self.parameters`) and `value` is the value
                or function to assign.

        Returns:
            simulation: the `Simulation` class specified by the arguments provided.

        Raises:
            SystemError: if the system has not been compuled.
        """
        if not self.compiled:
            raise SystemError(f"System has not been compiled.")
        if params := self._check_required_parameters() - input_parameters.keys():
            warnings.warn(
                f"The parameters {params} have no default value. This must be provided before a simulation run."
            )
        simulation = Simulation(self, solver, initial_values, input_parameters)
        if name:
            self.simulations.update({name: simulation})
        return simulation

    def _get_symbols(
        self, variable_assignments, parameter_assignments, required_inputs
    ):
        """
        Returns all variable and parameter symbols.
        """
        variables = {assg.variable.symbol for assg in variable_assignments}
        parameters = {assg.parameter.symbol for assg in parameter_assignments}
        required_inputs = {parameter.symbol for parameter in required_inputs}
        return variables, parameters | required_inputs

    def _process_parameter_assignment(self, assignment) -> str:
        """
        Returns the type of an assignment. Called for a particular ported object P:

        - "functional", if it is internally defined and can't be updated.
        - "default_exposable", if it is a default assignment associated to some nested child of P
        - "default_optional", if it is a default assignment associated to P
        - "composite", if it is none of the above (should never return this).

        """
        if isinstance(assignment, FunctionalAssignment):
            type = "functional"
        elif isinstance(assignment, DefaultParameterAssignment):
            if HIERARCHY_SEPARATOR in assignment.name:
                type = "default_exposable"
            else:
                type = "default_optional"
        else:
            type = "composite"

        return type

    def _reset_variables_parameters(self):
        self.variables = Container()
        self.parameters = Container()

    def _create_simulation_variables(self, variable_assignments, variables, parameters):
        """
        Creates a simulation variable and an update rule for each variable assignment,
        stored in `self.variables`.
        """
        for assg in variable_assignments:
            update_rule = UpdateRule(assg.expression, variables, parameters)
            sim_variable = SimVariable(assg.variable)
            sim_variable.set_update_rule(update_rule)
            self.variables[assg.variable.symbol] = sim_variable

    def _create_simulation_parameters(
        self, parameter_assignments, variables, parameters
    ):
        """
        Creates a simulation parameter and update rule for each parameter assignment,
        stored in `self.parameters`.
        """
        for assg in parameter_assignments:
            parameter_type = self._process_parameter_assignment(assg)
            sim_parameter = SimParameter(assg.parameter, parameter_type)
            sim_parameter.initialise_update_rule(variables, parameters)
            self.parameters[assg.parameter.symbol] = sim_parameter

    def _create_input_parameters(self, required_inputs):
        """
        Creates a simulation parameter and empty update rule for each required input,
        meaning anything coming from an input port of a compiled object with no default
        value. It is stored in `self.parameters`.
        """
        for input in required_inputs:
            sim_parameter = SimParameter(input, "required")
            sim_parameter.initialise_update_rule(set(), set())
            self.parameters[input.symbol] = sim_parameter

    def compute_parameter_update_order(self) -> list[Symbol]:
        """
        Computes the dependency tree of parameters in `self.parameters`.

        By performing a topological sort, the correct substitution order of parameters
        is determined. For example if `par_a = f(par_b)` and `par_b = g(par_c)`, the 
        substitution `par_b -> g(par_c)` must be performed before `par_a -> f(par_b)`.

        If a topologial sort fails, there are cyclic dependencies in the parameter tree
        and an exception is raised. 

        Returns:
            nodes: the keys of `self.parameters` in sorted order.

        Raises:
            SystemError: if there are cyclic dependencies. 
        """
        variable_symbols = set(self.variables.keys())
        parameter_symbols = self.parameters
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters.values():
            parsym = parameter.symbol
            for dependency in parameter.dependent_parameters:
                if dependency in parameter_symbols:
                    G.add_edge(dependency, parsym)
                elif dependency not in (variable_symbols | {self.time.symbol}):
                    raise SystemError(
                        f"Parameter {parsym} references undefined symbol {dependency}"
                    )
        try:
            nodes = list(nx.topological_sort(G))
        except nx.exception.NetworkXUnfeasible:
            raise SystemError(f"System parameters contain cyclic dependencies")
        return nodes

    def get_readable_symbols(self) -> tuple[dict, dict]:
        """
        Generates short symbols for the variables and parameters in the system.

        - Variables are mapped to `x_i`, where `i` is incremented for each variable.
        - Parameters are mapped to `a_i`, where `i` is incremented for each parameter.

        warning: Warning
            This is currently a very crude implementation. In the future, a lot more
            customisation will be offered.

        Returns:
            vars_dict: a mapping of variable symbols to readable variable symbols
            pars_dict: a mapping of parameter symbols to readable parameter symbols
        """
        vars_dict = {v: Symbol(f"x_{i}") for i, v in enumerate(self.variables)} | {
            self.time.symbol: Symbol("t")
        }
        pars_dict = {p: Symbol(f"a_{i}") for i, p in enumerate(self.parameters)}
        return vars_dict, pars_dict

    def get_readout(self, vars_dict: dict = None, pars_dict: dict = None) -> str:
        """
        Get a LaTeX-readable summary of the system ODEs and functions.
        """
        if not vars_dict:
            vars_dict, _ = self.get_readable_symbols()
        if not pars_dict:
            _, pars_dict = self.get_readable_symbols()
        odes = [
            var.get_readout(self.time.symbol, vars_dict, pars_dict)
            for var in self.variables.values()
        ]
        functions = [
            par.get_readout(vars_dict, pars_dict) for par in self.parameters.values()
        ]
        print(f"system ODEs: \[{self._combine_latex(*odes)}\]")
        print(f"system functions: \[{self._combine_latex(*functions)}\]")
        print(f"variable mappings: {vars_dict}")
        print(f"parameter mappings: {pars_dict}")

    def _combine_latex(self, *equations) -> str:
        n = len(equations)
        if n == 0:
            return ""
        l1 = r"\left\{\begin{matrix}%s\end{matrix}\right."
        l2 = r" \\ ".join(eq for eq in equations)
        return l1 % l2

    def __repr__(self) -> str:
        vars_dict, pars_dict = self.get_readable_symbols()
        odes = [
            var.get_readout(self.time.symbol, vars_dict, pars_dict, type="default")
            for var in self.variables.values()
        ]
        functions = [
            par.get_readout(vars_dict, pars_dict, type="default")
            for par in self.parameters.values()
        ]
        readout = (
            f"system ODEs: {odes} \n"
            + f"system functions: {functions} \n"
            + f"variable mappings: {vars_dict} \n"
            + f"parameter mappings: {pars_dict}"
        )
        return readout

    def to_data(self) -> SystemData:
        """
        Map the system to a `SystemData` instance. Not currently used for anything.

        Returns:
            data: a `SystemData` instance.
        """
        metadata = {"compiled": self.compiled}
        ported_object = self.ported_object_data
        return SystemData(metadata=metadata, ported_object=ported_object)
