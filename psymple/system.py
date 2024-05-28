from bisect import bisect
from scipy.integrate import solve_ivp
from numpy import linspace

import matplotlib.pyplot as plt
import networkx as nx

from psymple.globals import T
from psymple.variables import (
    Parameter,
    Parameters,
    SimParameter,
    SimUpdateRule,
    SimVariable,
    Variable,
    Variables,
    UpdateRules,
)

from psymple.ported_objects import (
    ParameterAssignment,
    DifferentialAssignment,
    PortedObject,
)


class PopulationSystemError(Exception):
    pass


class System:
    def __init__(self, ported_object):
        self.variables = {}
        self.parameters = {}

        assert isinstance(ported_object, PortedObject)
        compiled = ported_object.compile()

        self.create_time_variable()

        variable_assignments, parameter_assignments = compiled.get_assignments()

        variables, parameters = self.get_symbol_containers(variable_assignments, parameter_assignments)
        self.create_simulation_variables(variable_assignments, variables + self.time, parameters)
        self.create_simulation_parameters(parameter_assignments, variables + self.time, parameters)
        self.update_update_rules()

    def create_time_variable(self):
        # At the moment the only global variable is time
        self.time = SimVariable(Variable(T, 0.0, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                #self.time,
                equation="1",
                variables=Variables(),
                parameters=Parameters(),
                description="system time",
            )
        )

    def get_symbol_containers(self, variable_assignments, parameter_assignments):
        variables = [SimVariable(assg.variable) for assg in variable_assignments]
        parameters = [SimParameter(assg.parameter) for assg in parameter_assignments]
        return Variables(variables), Parameters(parameters)

    def create_simulation_variables(self, variable_assignments, variables, parameters):
        for assg in variable_assignments:
            update_rule = assg.to_update_rule(variables, parameters)
            sim_variable = SimVariable(assg.variable)
            sim_variable.set_update_rule(update_rule)
            self.variables[str(assg.variable.symbol)] = sim_variable

    def create_simulation_parameters(self, parameter_assignments, variables, parameters):
        for assg in parameter_assignments:
            sim_parameter = SimParameter(assg.parameter)
            sim_parameter.initialize_update_rule(variables, parameters)
            self.parameters[str(assg.parameter.symbol)] = sim_parameter 

    def update_update_rules(self):
        variables = Variables(list(self.variables.values()))
        parameters = Parameters(list(self.parameters.values()))
        for var in self.variables.values():
            new_update_rule = SimUpdateRule.from_update_rule(var.update_rule, variables + self.time, parameters)
            var.set_update_rule(new_update_rule)
        for par in self.parameters.values():
            par.initialize_update_rule(variables + self.time, parameters)

    def _compute_parameter_update_order(self):
        variable_symbols = {v.symbol for v in self.variables.values()} | {T}
        # print("params")
        # for par in self.parameters:
        #     print(type(par), par)
        parameter_symbols = {p.symbol: p for p in self.parameters.values()}
        # print("param symbol")
        # for symbol in parameter_symbols:
        #     print(type(symbol), symbol)
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters.values():
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
        except nx.exception.NetworkXUnfeasible:
            raise PopulationSystemError(
                f"System parameters contain cyclic dependencies"
            )
        return list(nodes)



class Simulation:
    def __init__(self, system, solver = "discrete_int"):
        self.system = system
        self.variables = system.variables
        self.parameters = system.parameters
        self.time = system.time
        self.solver = solver

    def _compute_substitutions(self):
        update_order = [str(par) for par in self.system._compute_parameter_update_order()]
        print(update_order)
        variables = Variables(list(self.variables.values())) + self.time
        for parameter in update_order:
            self.parameters[parameter].substitute_parameters(variables)
        for variable in self.variables.values():
            variable.substitute_parameters(variables)

    #TODO: Remove variable dependency from update_rule

    def simulate(self, t_end, **options):
        self._compute_substitutions()
        if self.solver == "discrete_int":
            assert "n_steps" in options.keys() 
            n_steps = options["n_steps"]
            solver = DiscreteIntegrator(self, t_end, n_steps)
        solver.run()

    def plot_solution(self, variables, t_range=None):
        t_series = self.time.time_series
        if t_range is None:
            sl = slice(None, None)
        else:
            lower = bisect(t_series, t_range[0])
            upper = bisect(t_series, t_range[1])
            sl = slice(lower, upper)
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


class Solver:
    def __init__(self, simulation, t_end):
        if t_end <= 0 or not isinstance(t_end, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{t_end}'."
            )
        self.t_end = t_end
        self.simulation = simulation

class DiscreteIntegrator(Solver):
    def __init__(self, simulation, t_end, n_steps):
        super().__init__(simulation, t_end)
        self.n_steps = n_steps

    def run(self):
        for i in range(self.t_end):
            self._advance_time_unit(self.n_steps)

    def _advance_time(self, time_step):
        self.simulation.time.update_buffer()
        for variable in self.simulation.variables.values():
            variable.update_buffer()
        for variable in self.simulation.variables.values():
            variable.update_time_series(time_step)
        self.simulation.time.update_time_series(time_step)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)


'''
class System_old:
    def __init__(
        self, population=None, variable_assignments=[], parameter_assignments=[]
    ):
        self.time = SimVariable(Variable(T, 0.0, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                self.time,
                "1",
                Variables(),
                Parameters(),
                "system time",
            )
        )
        if population is not None:
            self.variables = self._create_variables(population.variables)
            self.parameters = self._create_parameters(population.parameters)
            self._assign_update_rules(population.update_rules)
        else:
            self._create_from_assignments(variable_assignments, parameter_assignments)

    def _create_from_assignments(self, variable_assignments, parameter_assignments):
        variables = []
        for assg in variable_assignments:
            assert isinstance(assg, DifferentialAssignment)
            assert isinstance(assg.variable, Variable)
            variables.append(assg.variable)
            # print(assg)
        variables = Variables(variables)

        parameters = []
        for assg in parameter_assignments:
            assert isinstance(assg, ParameterAssignment)
            assert isinstance(assg.parameter, Parameter)
            parameters.append(assg.parameter)
            # print(assg)
        parameters = Parameters(parameters)

        self.variables = self._create_variables(variables)
        self.parameters = self._create_parameters(parameters)
        update_rules = UpdateRules(
            [
                assg.to_update_rule(self.variables, self.parameters)
                for assg in variable_assignments + parameter_assignments
            ]
        )
        self._assign_update_rules(update_rules)

    def _create_variables(self, variables):
        for variable in variables:
            if variable.initial_value is None:
                print(f"Warning: Variable {variable.symbol} has no initial value")
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
            parameter.initialize_update_rule(
                self.variables + self.time, self.parameters
            )

    def _compute_parameter_update_order(self):
        variable_symbols = {v.symbol for v in self.variables + self.time}
        # print("params")
        # for par in self.parameters:
        #     print(type(par), par)
        parameter_symbols = {p.symbol: p for p in self.parameters}
        # print("param symbol")
        # for symbol in parameter_symbols:
        #     print(type(symbol), symbol)
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

    def _wrap_for_solve_ivp(self, t, y):
        """
        returns a callable function of all system variables for use with solve_ivp,
        wrapping lambdified update rules
        """
        for variable in self.variables:
            if variable.update_rule._equation_lambdified is None:
                variable.update_rule._lambdify()

        return [
            v.update_rule._equation_lambdified(
                **{
                    p: y[self.variables.objects.index(self.variables[p])]
                    if p != "T"
                    else t
                    for p in v.update_rule._equation_lambdified.__code__.co_varnames
                }
            )
            for v in self.variables
        ]

    def _advance_time(self, time_step):
        self.time.update_buffer()
        for variable in self.variables:
            variable.update_buffer()
        for variable in self.variables:
            variable.update_time_series(time_step)
        self.time.update_time_series(time_step)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)

    def simulate(self, t_end, n_steps, mode="dscr"):
        if t_end <= 0 or not isinstance(t_end, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{t_end}'."
            )
        self._compute_substitutions()
        if mode == "discrete" or mode == "dscr":
            print("dscr")
            for i in range(t_end):
                self._advance_time_unit(n_steps)
        elif mode == "continuous" or mode == "cts":
            print("cts")
            sol = solve_ivp(
                self._wrap_for_solve_ivp,
                [0, t_end],
                self.variables.get_final_values(),
                dense_output=True,
            )
            t = linspace(0, t_end, n_steps * t_end + 1)
            self.time.time_series = t
            for variable in self.variables:
                variable.time_series = sol.sol(t)[
                    self.variables.objects.index(variable)
                ]

    def plot_solution(self, variables, t_range=None):
        t_series = self.time.time_series
        if t_range is None:
            sl = slice(None, None)
        else:
            lower = bisect(t_series, t_range[0])
            upper = bisect(t_series, t_range[1])
            sl = slice(lower, upper)
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
'''