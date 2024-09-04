from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psymple.build import System

from bisect import bisect
from copy import deepcopy
from time import time

import matplotlib.pyplot as plt

from psymple.abstract import ParsingError

from psymple.variables import Container

from .solvers import (
    DiscreteIntegrator,
    ContinuousIntegrator,
    SOLVER_ALIASES,
)

from sympy import (
    parse_expr,
    Number,
)


class SetterObject:
    """
    Base class handling the updating of attributes of parameters and variables.

    Methods:
        set_parameters
        set_initial_values
    """
    def set_parameters(self, parameter_values: dict[str, str | int | float] = {}):
        """
        Set input parameters.

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
        for parameter, value in parameter_values.items():
            parameter = self.parameters[parameter]
            if isinstance(value, str):
                value = parse_expr(
                    value, local_dict=self.system_parameters | self.utility_functions
                )
            elif isinstance(value, (int, float)):
                value = Number(value)
            else:
                raise TypeError(f"Parameter {parameter.name} was provided value {value} "
                                f"of type {type(value)} which is not of type [str, float, int].")
            if bad_symbols := (
                value.free_symbols
                - {self.time.symbol}
                - set(self.system_parameters.values())
            ):
                raise ParsingError(f"The symbols {bad_symbols} cannot be used.")
            if parameter.type in {"default_optional", "default_exposable", "required"}:
                parameter.change_parameter_value(value, {self.time.symbol}, value.free_symbols - {self.time.symbol})
                parameter.type = "default_optional"
            else:
                raise TypeError(
                    f"The value of parameter {parameter.name} is fixed and cannot be updated."
                )
    
    def set_initial_values(self, initial_values: dict[str, int | float]):
        """
        Set initial values.

        Initial values must be `int` or `float` instances only.

        Args:
            initial_values: a dictionary of `variable: value` pairs where `variable` is the string
                identifier of a variable in `self.variables` and `value` is `int` or `float`.
        """
        for var, value in initial_values.items():
            self.variables[var].initial_value = value

class Simulation(SetterObject):
    """
    A Simulation is a basic object which produces a simulable system which is passed to a solver.

    Methods:
        simulate
        plot_solution

    info: Information:
        The simulation capability of `psymple` is fairly rudimentary. These features are currently
        designed to exemplify the functionality of the rest of the package.
    """

    def __init__(
        self,
        system: System,
        solver: str = "continuous",
        initial_values: dict = {},
        input_parameters: dict = {},
    ):
        """
        Create a Simulation instance.

        Args:
            system: the system to simulate
            solver: solver type
            initial_values: initial values
            input_parameters: input_parameters
        """
        self.variables = deepcopy(system.variables)
        self.parameters = self._create_ordered_parameters(
            system.parameters, system.compute_parameter_update_order()
        )
        self.time = deepcopy(system.time)

        self.solver = solver

        self.system_parameters = deepcopy(system.system_parameters)
        self.utility_functions = deepcopy(system.utility_functions)
        self.set_initial_values(initial_values)
        self.set_parameters(input_parameters)
        
        self.lambdify_ns = deepcopy(system.lambdify_ns)
        self.solver_symbols = system.get_readable_symbols()

    def _create_ordered_parameters(self, parameters, order):
        parameters = deepcopy(parameters)
        ordered_parameters = Container({p: parameters[p] for p in order})
        return ordered_parameters

    def _compute_substitutions(self):
        """
        Perform symbolic substitutions replacing `symbol -> value` in every
        update rule of every parameter and variable object, for every
        `(symbol, value)` pair in `self.parameters`.
        """
        for parameter in self.parameters.values():
            self._substitute_parameters(parameter.update_rule)
        for variable in self.variables.values():
            self._substitute_parameters(variable.update_rule)

    def _substitute_parameters(self, update_rule):
        """
        Perform substitutions and re-initialise dependencies.
        """
        update_rule.expression = update_rule.expression.subs(
            ((p, self.parameters[p].expression) for p in update_rule.parameters)
        )
        update_rule._initialise_dependencies(
            set(self.variables.keys()) | {self.time.symbol}, set()
        )
        update_rule._equation_lambdified = None

    def simulate(self, t_end: int, print_solve_time: bool = False, **options):
        """
        Simulate a system by calling the instance of `Solver` specified by `self.solver`. Currently, 
        this is either a discrete (Euler forward) integrator, or a a continuosu integrator implemented
        as a call to `scipy.integrate.solve_ivp`.

        Args:
            t_end: when to terminate the simulation. Currently this must be a positive integer.
            print_solve_time: if `True`, the time taken by the solver will be printed in the terminal.
            **options: options to pass to the `Solver` instance.
        """
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

    def plot_solution(self, variables: list | dict = None, t_range: list = None):
        """
        Produce a simple solution plot of time against a selection of variables.

        Args:
            variables: a `list` of keys identifying variables in `self.variables`, or a `dict` of
                `key: option` pairs, where `key` identifies a variable in `self.variables` and
                `option` is a `str` or `dict` which is passed to `matplotlib.pyplot.plot`. If `None`,
                all variables are plotted on the same axes.
            t_range: a list of the form `[t_start, t_end]` defining the range displayed on the time
                axis. If `None`, the time axis is determined by `self.variables.time.time_series`.
        """
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
