import networkx as nx
from models.globals import T
from models.variables import (
    Parameters,
    SimParameter,
    SimUpdateRule,
    SimVariable,
    UpdateRule,
    UpdateRules,
    Variable,
    Variables,
)


class PopulationSystemError(Exception):
    pass


class System:
    def __init__(self, population):
        self.time = Variable(T, 0, "system time")
        self.variables = self._create_variables(population.variables + self.time)
        self.parameters = self._create_parameters(population.parameters)
        self._assign_update_rules(population.update_rules)

    def _create_variables(self, variables):
        return Variables([SimVariable(variable) for variable in variables])

    def _create_parameters(self, parameters):
        return Parameters([SimParameter(parameter) for parameter in parameters])

    def _assign_update_rules(self, update_rules):
        new_update_rules = UpdateRules(
            [SimUpdateRule(update_rule) for update_rule in update_rules]
        )
        for rule in new_update_rules:
            rule.variable = self.variables[rule.variable.symbol]
        for variable in self.variables:
            updates_for_variable = [
                update for update in new_update_rules if update.variable == variable
            ]
            variable.update_rule = new_update_rules._combine(
                variable, updates_for_variable
            )
            (
                variable.update_rule.variables,
                variable.update_rule.parameters,
            ) = UpdateRule._get_dependencies(
                variable.update_rule.equation, self.variables, self.parameters
            )

    def _compute_parameter_update_order(self):
        variable_symbols = {v.symbol for v in self.variables}
        parameter_symbols = {p.symbol: p for p in self.parameters}
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters:
            parsym = parameter.symbol
            dependencies = parameter.value.free_symbols
            for dependency in dependencies:
                if dependency in parameter_symbols:
                    G.add_edge(dependency, parsym)
                elif dependency not in variable_symbols:
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

    def _compute_parameters(self):
        self.parameters = Parameters(self._compute_parameter_update_order())
        sub_list = []
        for parameter in self.parameters:
            parameter.computed_value = parameter.value.subs(sub_list)
            sub_list.append((parameter.symbol, parameter.computed_value))

    def _sub_parameters(self):
        for variable in self.variables:
            variable.sub_parameters()

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
        for variable in self.variables:
            variable.update_buffer()
        for variable in self.variables:
            variable.update_time_series(time_step)
        time_symbol = self.time.symbol
        self.variables[time_symbol].time_series.append(
            self.variables[time_symbol].time_series[-1] + time_step
        )

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)

    def simulate(self, t_end, n_steps):
        self._compute_parameters()
        self._sub_parameters()
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(t_end):
            self._advance_time_unit(n_steps)
