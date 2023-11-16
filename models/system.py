import networkx as nx

from models.globals import T
from models.variables import (
    Parameters,
    SimParameter,
    SimUpdateRule,
    SimVariable,
    Variable,
    Variables,
)


class PopulationSystemError(Exception):
    pass


class System:
    def __init__(self, population):
        self.time = SimVariable(Variable(T, 0, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                self.time,
                "1",
                Variables(),
                Parameters(),
                "system time",
            )
        )
        self.variables = self._create_variables(population.variables)
        self.parameters = self._create_parameters(population.parameters)
        self._assign_update_rules(population.update_rules)

    def _create_variables(self, variables):
        for variable in variables:
            if variable.initial_value is None:
                # print(f"Warning: Variable {variable.symbol} has no initial value")
                variable.initial_value = 0
        return Variables([SimVariable(variable) for variable in variables])

    def _create_parameters(self, parameters):
        for parameter in parameters:
            if parameter.value is None:
                raise PopulationSystemError(
                    f"Parameter {parameter.symbol} has no value"
                )
        return Parameters([SimParameter(parameter) for parameter in parameters])

    def _assign_update_rules(self, update_rules):
        combined_update_rules = update_rules._combine_update_rules()
        for rule in combined_update_rules:
            new_rule = SimUpdateRule.from_update_rule(
                rule, self.variables + self.time, self.parameters
            )
            # variable = self.variables[rule.variable.symbol]
            variable = new_rule.variable
            variable.set_update_rule(new_rule)
        for variable in self.variables:
            if variable.update_rule is None:
                # print(f"Warning: Variable {variable.symbol} has no update rule.")
                variable.set_update_rule(SimUpdateRule(variable))
        for parameter in self.parameters:
            parameter.initialize_update_rule(self.variables, self.parameters)

    def _compute_parameter_update_order(self):
        variable_symbols = {v.symbol for v in self.variables + self.time}
        parameter_symbols = {p.symbol: p for p in self.parameters}
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters:
            parsym = parameter.symbol
            for dependency in parameter.dependent_parameters():
                if dependency.symbol in parameter_symbols:
                    G.add_edge(dependency.symbol, parsym)
                elif dependency.symbol not in variable_symbols:
                    raise PopulationSystemError(
                        f"Parameter {parsym} references undefined symbol {dependency}"
                    )
        try:
            nodes = nx.topological_sort(G)
            ordered_parameters = [parameter_symbols[n] for n in nodes]
        except nx.exception.NetworkXUnfeasible:
            raise PopulationSystemError(
                f"System parameters contain cyclic dependencies"
            )
        return ordered_parameters

    def _compute_substitutions(self):
        self.parameters = Parameters(self._compute_parameter_update_order())
        for parameter in self.parameters:
            parameter.substitute_parameters(self.variables + self.time)
        for variable in self.variables:
            variable.substitute_parameters(self.variables + self.time)

    def _wrap_for_solve_ivp(self, *args):
        """
        returns a callable function of all system variables for use with solve_ivp,
        wrapping lambdified update rules
        """
        # FIXME: doesn't work with the solve_ivp function call signature of
        # f(t,[y0,y1,...]) yet. Needs a deeper think about how time
        # is handled generally.
        return [
            u._equation_lambdified(
                [
                    args[i]
                    for i in [self.variables.objects.index(v) for v in u.variables]
                ]
            )
            for u in self.update_rules
        ]

    def _advance_time(self, time_step):
        self.time.update_buffer()
        self.time.update_time_series(time_step)
        for variable in self.variables:
            variable.update_buffer()
        for variable in self.variables:
            variable.update_time_series(time_step)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)

    def simulate(self, t_end, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{n_steps}'."
            )
        self._compute_substitutions()
        for i in range(t_end):
            self._advance_time_unit(n_steps)
