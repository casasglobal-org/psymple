from bisect import bisect
from scipy.integrate import solve_ivp
from numpy import linspace
from copy import deepcopy
from abc import ABC, abstractmethod
from time import time
from inspect import signature

import warnings

import matplotlib.pyplot as plt
import networkx as nx
import sympy as sym

#from psymple.globals import T, sym_custom_ns
from psymple.variables import (
    Parameter,
    SimParameter,
    SimUpdateRule,
    SimVariable,
    Variable,
    Container,
)

from psymple.ported_objects import (
    ParameterAssignment,
    DifferentialAssignment,
    PortedObject,
    DefaultParameterAssignment,
    FunctionalAssignment,
    HIERARCHY_SEPARATOR,
)

from psymple.io.create_system import System_Creator

SOLVER_ALIASES = {
    "discrete": [
        "discrete",
        "discrete",
        "dscr",
        "disc",
        "discr",
    ],
    "continuous": [
        "continuous",
        "cts",
        "cont",
        "scipy",
    ],
    "proceedural": [
        "proceedural",
        "proc",
    ],
}


class SystemError(Exception):
    pass


class System(System_Creator):
    """
    Core class for creating, storing and simulating a model. 

    Methods:
        add_system_parameter
        add_utility_function
        add_object
        compile
        create_simulation
        get_readout
    """
    def __init__(self, data={}, utility_functions = [], system_parameters = [], time_symbol = "T"):
        """
        Create a system.

        Args:
            data: data parametrising a collection of ported objects in a format accepted by System_Creator class
            utility_functions: data specifying the utility functions available in the system. Must be a list
                of dictionary or tuple objects. A dictionary must specify name, function and optionally signature
                attributes. A tuple will be read in order of name, function and signature. See documentation for
                add_utility_function for acceptable values.
            system_paramters: data specifying the system parameters available in the system. Must be a list
                of dictionary or tuple objects. A dictionary must specify name, function and optionally signature
                attributes. A tuple will be read in order of name, function and signature. See documentation for
                add_system_paramter for acceptable values.
            time_symbol: The symbol used for the independent variable time in the system. Defaults to T.
        """
        super().__init__()
        self.variables = Container()
        self.parameters = Container()
        self.lambdify_ns = ["numpy", "scipy"]
        self.system_parameters = {}
        self.utility_functions = {}
        self.compiled = False
        self.simulations = {}

        if time_symbol != "T":
            warnings.warn(f"time symbol {time_symbol} has not been tested. Reverting back to T.")
            time_symbol = "T"
        self._create_time_variable(time_symbol)

        self._add_function("utility_function", *utility_functions)
        self._add_function("system_parameter", *system_parameters)

        self.add_object(data)

    def add_system_parameter(self, name: str, function, signature: tuple = None):
        """
        A system parameter is a system-wide function which may only depend on the independent system variable time or
        other system parameters. These functions are not syntactically callable, rather they are shorthand for
        functions of time and other system parameters.

        If function is callable, the signature should be provided if the function arguments names are not system 
        parameters or time. Acceptable inputs:

        >>> system.add_system_parameter("T_avg", lambda T_min, T_max: (T_min + T_max)/2)
        >>> system.add_system_parameter("T_avg", lambda a, b: (a+b)/2, signature=("T_min", "T_max"))

        Not acceptable:

        >>> system.add_system_paramter("T_avg", lambda a, b: (a+b)/2)

        If the function is symbolic, a signature only needs to be provided to control the display order of the
        function arguments. If not provided, the generation of the signature does not preserve the order in
        which the symbols appear. This does not affect the computation of the system parameter. For example,

        >>> system.add_system_parameter("T_ratio", "T_max / T_min")

        will always compute `T_ratio = T_max / T_min`, but may display as `T_ratio (T_max, T_min)` or
        `T_ratio (T_min, T_max)`.

        The provided signature must be a list or tuple containing exactly the symbols in the expression in the
        required order.

        >>> system.add_system_parameter("T_ratio", "T_max / T_min", ("T_max", "T_min"))
        >>> print(system.system_parameters)

        Then whenever `T_ratio` is written in an assignment definition, it will be interpreted and displayed
        as the function `T_ratio(T_max, T_min)`.
        """
        if name in self.system_parameters:
            warnings.warn(
                f"The system parameter {name} has already been defined. It will be overwritten."
            )
        if callable(function):
            # T_avg, lambda T_min, T_max: T_min + T_max / 2
            args, nargs = self._inspect_signature(function)
            # args = T_min, T_max, nargs = (2,)
            if signature:
                print(signature, args, nargs, len(signature) in nargs)
                if signature != args:
                    if len(signature) not in nargs:
                        raise ValueError(
                            f"Signature validation failed. The provided signature {signature}"
                            f"is not a length accepted by the provided function: {nargs}."
                        )
            else:
                signature = args
            # signature = (T_min, T_max)
            assert self._are_system_parameters(*signature)
            sym_func = self._add_callable_function(name, function, nargs=nargs)
        elif isinstance(function, str):
            # T_avg, T_max + T_min / 2
            sym_signature = self._generate_signature(function)
            if signature:
                assert set(signature) == set(sym_signature)
            else:
                warnings.warn(f"A signature for function {name} was not provided. The appearance of "
                              f"the function in displayed expressions may not be as expected.")
                signature = sym_signature
            # signature = T_max, T_min
            print(signature)
            assert self._are_system_parameters(*signature)
            sym_func = self._add_symbolic_function(name, function, signature)
        # The signature needs to take into account sub-dependencies of existing system parameters
        sig = tuple(sym.sympify(s, locals=self.system_parameters) for s in signature)
        self.system_parameters.update({name: sym_func(*sig)})

    def add_utility_function(self, name: str, function, signature: tuple = None):
        """
        A utility function is a system-wide function which can depend on any further created variable or parameter. 
        They expand functions available to the user when defining assignments.

        If function is callable, the signature will be inspected to determine the range of acceptable number of
        inputs. This is used to validate function entry in the creation of assignments.  

        >>> from numpy import sin
        >>> system.add_utility_function("new_sin": sin)

        Entering `new_sin(a,b)` in an assignment will raise an exception. 

        If function is symbolic, a signature should be provided if the order of function arguments matters.
        If not provided, the function may not behave as expected. The provided signature must be a list or 
        tuple containing exactly the symbols in the expression in the required order. For example,

        >>> system.add_utility_function("exp", "a**b")

        may evaluate as `exp(x,y) = x**y` or `exp(x,y) = y**x`. While,

        >>> system.add_utility_function("exp", "a**b", ("a", "b"))

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
                warnings.warn(f"A signature for function {name} was not provided. The behaviour of "
                               "the function may not be as expected.")
                signature = sym_signature           
            sym_func = self._add_symbolic_function(name, function, signature)
        self.utility_functions.update({name: sym_func})

    def compile(self, ported_object = None):
        """
        Compile the system at the specified ported object. This will compile the specified ported object,
        and then create the necessary variables and parameters for simulation.

        Args:
            ported_object: an instance of PortedObject or a string identifying a ported object from
            self.ported_objects. If not provided, the most recent ported object added to self will
            be used.
        """
        if ported_object:
            if isinstance(ported_object, str):
                ported_object = self.get_system(ported_object)
        else:
            ported_object = self.get_system()
        try:
            compiled = ported_object.compile()
        except:
            raise SystemError("Unable to compile ported object {ported_object}")
        variable_assignments, parameter_assignments = compiled.get_assignments()
        # self.sub_system_parameters(variable_assignments, parameter_assignments)

        self.process_parameter_assignments(parameter_assignments, compiled.input_ports)

        variables, parameters = self.get_symbols(
            variable_assignments, parameter_assignments
        )
        self.create_simulation_variables(
            variable_assignments, variables | {self.time.symbol}, parameters
        )
        self.create_simulation_parameters(
            parameter_assignments, variables | {self.time.symbol}, parameters
        )
        self.compiled = True

    def create_simulation(self, name = None, solver = "discrete", initial_values: dict = None):
        if self.compiled:
            simulation = Simulation(self, solver, initial_values)
            if name:
                self.simulations.update({name: simulation})
            return simulation
        else:
            raise SystemError(f"System has not been compiled.")

    def add_object(self, data, parameters={}, utilities={}):
        sympify_locals = (
            self.system_parameters | parameters | self.utility_functions | utilities
        )
        if isinstance(data, PortedObject):
            self._process(data.dumps(), sympify_locals)
        elif isinstance(data, dict):
            self._process(data, sympify_locals)
        else:
            raise TypeError(f"Unsupported data type {type(data)}.")

    """
    def sub_system_parameters(self, variable_assignments, parameter_assignments):
        for assg in variable_assignments + parameter_assignments:
            print("expr",assg.expression)
            print("system params",self.system_parameters)
            assg.expression = assg.expression.subs(self.system_parameters)
    """

    def _create_time_variable(self, time_symbol):
        # At the moment the only global variable is time
        time_symbol = sym.Symbol(time_symbol)
        self.time = SimVariable(Variable(time_symbol, 0, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                equation="1",
                variables={},
                parameters={},
                description="system time",
            )
        )

    def _add_function(self, type, *data):
        print(data)
        for function_data in data:
            if isinstance(function_data, dict):
                pass
            elif isinstance(function_data, tuple):
                    print(function_data)
                    function_data = {                          
                        "name": function_data[0],
                        "function": function_data[1],
                        "signature": function_data[2] if len(function_data) == 3 else None
                    }
                    print(function_data)
            else:
                raise SystemError(f"Function creation data {function_data} must be of type "
                                  f"tuple or dict.")
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
        self.lambdify_ns.insert(0, {name: callable})
        sym_func = sym.Function(f"{name}", nargs=nargs)
        return sym_func

    def _inspect_signature(self, callable):
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

    def _generate_signature(self, expression):
        expression = sym.sympify(expression)
        signature = expression.free_symbols
        return tuple(symbol.name for symbol in signature)

    def _are_system_parameters(self, *params):
        return any([param in self.system_parameters | {self.time.symbol.name: 0} for param in params])

    def _add_symbolic_function(
        self, name: str, expression=None, signature: list | tuple = None
    ):

        signature = sym.symbols(signature)
        callable = sym.lambdify(signature, expression, modules=self.lambdify_ns)

        self.lambdify_ns.insert(0, {name: callable})

        sym_func = sym.Function(f"{name}", nargs=(len(signature),))
        return sym_func

        # Not implemented
        # assg = FunctionalAssignment(name, expr)
        # self.functional_assignments.update({name: assg})

    def get_symbols(self, variable_assignments, parameter_assignments):
        variables = {assg.variable.symbol for assg in variable_assignments}
        parameters = {assg.parameter.symbol for assg in parameter_assignments}
        return variables, parameters

    def process_parameter_assignments(self, parameter_assignments, input_ports):
        parameters = {
            "functional": [],
            "composite": [],
            "default exposable": [],
            "default optional": [],
            "required": [],
        }

        for assg in parameter_assignments:
            if isinstance(assg, FunctionalAssignment):
                parameters["functional"].append(assg.name)
            elif isinstance(assg, DefaultParameterAssignment):
                if HIERARCHY_SEPARATOR in assg.name:
                    parameters["default exposable"].append(assg.name)
                else:
                    parameters["default optional"].append(assg.name)
            else:
                parameters["composite"].append(assg.name)

        parameters["required"] = [name for name in input_ports.keys()]

        # print(parameters)

    def create_simulation_variables(self, variable_assignments, variables, parameters):
        for assg in variable_assignments:
            update_rule = assg.to_update_rule(variables, parameters)
            sim_variable = SimVariable(assg.variable)
            sim_variable.set_update_rule(update_rule)
            self.variables[assg.variable.symbol] = sim_variable

    def create_simulation_parameters(
        self, parameter_assignments, variables, parameters
    ):
        for assg in parameter_assignments:
            sim_parameter = SimParameter(assg.parameter)
            sim_parameter.initialize_update_rule(variables, parameters)
            self.parameters[assg.parameter.symbol] = sim_parameter

    def _compute_parameter_update_order(self):
        variable_symbols = set(self.variables.keys())
        parameter_symbols = self.parameters
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters.values():
            parsym = parameter.symbol
            for dependency in parameter.dependent_parameters():
                if dependency in parameter_symbols:
                    G.add_edge(dependency, parsym)
                elif dependency not in variable_symbols:
                    raise SystemError(
                        f"Parameter {parsym} references undefined symbol {dependency}"
                    )
        try:
            nodes = nx.topological_sort(G)
        except nx.exception.NetworkXUnfeasible:
            raise SystemError(
                f"System parameters contain cyclic dependencies"
            )
        return nodes

    def get_readable_symbols(self):
        vars_dict = {v: sym.Symbol(f"x_{i}") for i, v in enumerate(self.variables)} | {
            self.time.symbol: sym.Symbol("t")
        }
        pars_dict = {p: sym.Symbol(f"a_{i}") for i, p in enumerate(self.parameters)}
        return vars_dict, pars_dict

    def get_readout(self, vars_dict: dict = None, pars_dict: dict = None):
        if not vars_dict:
            vars_dict, _ = self.get_readable_symbols()
        if not pars_dict:
            _, pars_dict = self.get_readable_symbols()
        odes = [
            var.get_readout(self.time.symbol, vars_dict, pars_dict) for var in self.variables.values()
        ]
        functions = [
            par.get_readout(vars_dict, pars_dict) for par in self.parameters.values()
        ]
        print(f"system ODEs: \[{self.combine_latex(*odes)}\]")
        print(f"system functions: \[{self.combine_latex(*functions)}\]")
        print(f"variable mappings: {vars_dict}")
        print(f"parameter mappings: {pars_dict}")

    def combine_latex(self, *equations):
        n = len(equations)
        if n == 0:
            return ""
        l1 = r"\left\{\begin{matrix}%s\end{matrix}\right."
        l2 = r" \\ ".join(eq for eq in equations)
        return l1 % l2

    def __repr__(self):
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
            f"system ODEs: {odes} \n "
            + f"system functions: {functions} \n "
            + f"variable mappings: {vars_dict} \n "
            + f"parameter mappings: {pars_dict}"
        )
        return readout


class Simulation:
    def __init__(self, system, solver="discrete", initial_values: dict = {}):
        self.system = system
        self.variables = deepcopy(system.variables)
        self.parameters = deepcopy(system.parameters)
        self.time = deepcopy(system.time)
        self.solver = solver
        self.set_initial_values(initial_values)

    def _compute_substitutions(self):
        update_order = list(self.system._compute_parameter_update_order())
        parameters = self.parameters
        for parameter in update_order:
            self._substitute_parameters(self.parameters[parameter].update_rule)
        for variable in self.variables.values():
            self._substitute_parameters(variable.update_rule)

    def _substitute_parameters(self, update_rule):
        # TODO: System method?
        update_rule.equation = update_rule.equation.subs(
            ((p, self.parameters[p].expression) for p in update_rule.parameters)
        )
        update_rule._initialize_dependencies(set(self.variables.keys()) | {self.time.symbol}, set())
        update_rule._equation_lambdified = None

    def set_initial_values(self, values: dict):
        for var in values:
            try:
                variable = self.variables[var]
            except:
                raise KeyError(f"{var} is not a system variable.")
            variable.time_series = [values[var]]

    def simulate(self, t_end, print_solve_time=False, **options):
        self._compute_substitutions()
        if self.solver in SOLVER_ALIASES["discrete"]:
            assert "n_steps" in options.keys()
            n_steps = options["n_steps"]
            solver = DiscreteIntegrator(self, t_end, n_steps)
        elif self.solver in SOLVER_ALIASES["continuous"]:
            solver = ContinuousIntegrator(self, t_end)
        elif self.solver in SOLVER_ALIASES["proceedural"]:
            raise NotImplementedError("proceedural solving is not implemented")
        else:
            raise NameError(
                f"The solver {self.name} is not recognised. Please use one "
                f"from {SOLVER_ALIASES.keys()}"
            )
        t_start = time()
        solver.run()
        t_end = time()
        if print_solve_time:
            print(
                f"Solution time with method '{self.solver}': {t_end - t_start} seconds."
            )

    def plot_solution(self, variables=None, t_range=None):
        t_series = self.time.time_series
        if t_range is None:
            sl = slice(None, None)
        else:
            lower = bisect(t_series, t_range[0])
            upper = bisect(t_series, t_range[1])
            sl = slice(lower, upper)
        if not variables:
            variables = {v: {} for v in self.variables}
        if isinstance(variables, set):
            variables = {v: {} for v in variables}
        legend = []
        for var_name, options in variables.items():
            variable = self.variables[var_name]
            if isinstance(options, str):
                plt.plot(t_series[sl], variable.time_series[sl], options)
            else:
                plt.plot(t_series[sl], variable.time_series[sl], **options)
            legend.append(variable.symbol.name)
        plt.legend(legend, loc="best")
        plt.xlabel("time")
        plt.grid()
        plt.show()


class Solver(ABC):
    def __init__(self, simulation, t_end):
        if t_end <= 0 or not isinstance(t_end, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{t_end}'."
            )
        self.t_end = t_end
        self.simulation = simulation

    @abstractmethod
    def run(self):
        pass


class DiscreteIntegrator(Solver):
    def __init__(self, simulation, t_end, n_steps):
        super().__init__(simulation, t_end)
        self.n_steps = n_steps

    def run(self):
        for i in range(self.t_end):
            self._advance_time_unit(self.n_steps)

    def _advance_time(self, time_step):
        self._update_buffer(self.simulation.time)
        for variable in self.simulation.variables.values():
            self._update_buffer(variable)
        for variable in self.simulation.variables.values():
            self._update_time_series(variable, time_step)
        self._update_time_series(self.simulation.time, time_step)

    def _update_buffer(self, variable):
        variable.buffer = variable.time_series[-1]

    def _update_time_series(self, variable, time_step):
        new_value = self._evaluate_update(
            variable.update_rule, variable.buffer, time_step
        )
        variable.time_series.append(new_value)

    def _evaluate_update(self, update_rule, old_value, time_step):
        value = self._evaluate_expression(update_rule)
        return old_value + value * time_step

    def _evaluate_expression(self, update_rule):
        if update_rule._equation_lambdified is None:
            update_rule._lambdify(self.simulation.system.lambdify_ns)
        # v_args = [self.simulation.variables[v].buffer if v is not self.time.symbol else self.simulation.time.buffer for v in update_rule.variables]
        v_args = {
            v.name: (
                self.simulation.variables[v].buffer
                if v is not self.simulation.time.symbol
                else self.simulation.time.buffer
            )
            for v in update_rule.variables
        }
        # All parameters have been substituted out. Keeping code for future proceedural solver
        # p_args = [self.simulation.parameters[p].computed_value for p in update_rule.parameters]
        # args = v_args + p_args
        return update_rule._equation_lambdified(**v_args)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)


class ContinuousIntegrator(Solver):
    def __init__(self, simulation, t_end):
        super().__init__(simulation, t_end)
        self.simulation._compute_substitutions()
        self._callable = self._wrap_for_solve_ivp()

    def _wrap_for_solve_ivp(self):
        """
        Return a callable function f(t,y) to pass to scipy.integrate representing
        the substituted ODE system dy/dt = f(t,y) with y a vector. For each x in y,
        dx/dt is computed as a lambdified expression of t and some subset
        (x_{i_1},...,x_{i_j}) of y.

        Function f can only take positional arguments, which are translated to
        keywords using fixed reference order in dictionary self.simulation.variables,
        filtered to each component function, and wrapped.
        """
        vars_dict, pars_dict = self.simulation.system.get_readable_symbols()
        for v in self.simulation.variables.values():
            v.update_rule.sub_symbols(vars_dict, pars_dict)
            if v.update_rule._equation_lambdified is None:
                v.update_rule._lambdify(self.simulation.system.lambdify_ns)

        ref_order = {
            vars_dict[key]: value for key, value in self.simulation.variables.items()
        }

        def callable(t, y):
            call_dict = {key: y[i] for i, key in enumerate(ref_order)} | {
                sym.symbols("t"): t
            }
            return [
                v.update_rule._equation_lambdified(
                    **{
                        var.name: value
                        for var, value in call_dict.items()
                        if var in v.update_rule.variables
                    }
                )
                for v in ref_order.values()
            ]

        return callable

    def run(self):
        # Initial values are defined as the most recent value in the time series
        initial_values = [v.time_series[-1] for v in self.simulation.variables.values()]
        res = solve_ivp(
            self._callable, [0, self.t_end], initial_values, dense_output=True
        )

        # Update time and variable time series with simulation result
        self.simulation.time.time_series = res.t
        for i, v in enumerate(self.simulation.variables.values()):
            v.time_series = res.y[i]
