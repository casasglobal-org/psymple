from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from psymple.simulate import Simulation

from .solver import Solver

class DiscreteIntegrator(Solver):
    """
    A forward Euler method integrator.

    warning: Warning
        This is a very rudimentary solver, and performs no accuracy checks or optimisation. It
        is primarily intended for prototyping or unit testing certain features since its 
        behaviour is fully controlled.
    """
    def __init__(self, simulation: Simulation, t_end: int, n_steps: int):
        """
        Create a `DiscreteIntegrator` instance.

        Args:
            simulation: an instance of `Simulation` to solve.
            t_end: positive integer at which to stop the simulation.
            n_steps: the number of substeps to compute per time unit.
        """
        super().__init__(simulation, t_end)
        self.n_steps = n_steps

    def run(self):
        """
        Run the solver according to its parameters.
        """
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
            update_rule._lambdify(self.simulation.lambdify_ns)
        v_args = [self.simulation.variables[v].buffer if v is not self.simulation.time.symbol else self.simulation.time.buffer for v in update_rule.variables]
        #v_args = {
        #    v.name: (
        #        self.simulation.variables[v].buffer
        #        if v is not self.simulation.time.symbol
        #       else self.simulation.time.buffer
        #    )
        #    for v in update_rule.variables
        #}
        # All parameters have been substituted out. Keeping code for future proceedural solver
        # p_args = [self.simulation.parameters[p].computed_value for p in update_rule.parameters]
        # args = v_args + p_args
        return update_rule._equation_lambdified(*v_args)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)

