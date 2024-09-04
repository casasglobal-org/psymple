from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from psymple.simulate import Simulation

from .solver import Solver

from numpy import arange

from sympy import symbols

from scipy.integrate import solve_ivp

class ContinuousIntegrator(Solver):
    """
    An interface to `scipy.integrate.solve_ivp`. The input from the simulation object is manipulated
    into a form acceptable by the `scipy` solver and run. 

    Attributes:
        _callable

    tip: Using another solver
        The attribute `_callable` created on instantiation is a function with signature `(t,y)` which 
        is a form accepted by, or easily coerced into, many other python-implemented ODE solvers.
    """
    def __init__(self, simulation: Simulation, t_end: int):
        """
        Create a `ContinuousIntegrator` instance.

        Args:
            simulation: an instance of `Simulation` to solve.
            t_end: positive integer at which to stop the simulation.
        """
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
        vars_dict, pars_dict = self.simulation.solver_symbols
        for v in self.simulation.variables.values():
            v.update_rule.sub_symbols(vars_dict, pars_dict)
            if v.update_rule._equation_lambdified is None:
                v.update_rule._lambdify(self.simulation.lambdify_ns)

        ref_order = {
            vars_dict[key]: value for key, value in self.simulation.variables.items()
        }

        def callable(t, y):
            call_dict = {key: y[i] for i, key in enumerate(ref_order)} | {
                symbols("t"): t
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
        """
        Run the solver according to its parameters.
        """
        # Initial values are defined as the most recent value in the time series
        initial_values = [v.time_series[-1] for v in self.simulation.variables.values()]
        res = solve_ivp(
            self._callable, [0, self.t_end], initial_values, dense_output=True
        )
        # Assign the interpolating solution object to the simulation
        self.simulation.solution = res.sol
        # Update time and variable time series with simulation result
        time_series = arange(0, self.t_end, 0.1)
        self.simulation.time.time_series = time_series
        for i, v in enumerate(self.simulation.variables.values()):
            v.time_series = res.sol(time_series)[i]