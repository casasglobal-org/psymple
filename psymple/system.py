from bisect import bisect
from scipy.integrate import solve_ivp
from numpy import linspace

import matplotlib.pyplot as plt
import networkx as nx
import sympy as sym

from psymple.globals import T
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
)


class PopulationSystemError(Exception):
    pass


class System:
    def __init__(self, ported_object):
        self.variables = Container()
        self.parameters = Container()

        assert isinstance(ported_object, PortedObject)
        compiled = ported_object.compile()

        self.create_time_variable()

        variable_assignments, parameter_assignments = compiled.get_assignments()

        from psymple.ported_objects import DefaultParameterAssignment
        print([p for p in parameter_assignments if isinstance(p,DefaultParameterAssignment)])

        self.required_input_ports = compiled.input_ports
        print(self.required_input_ports)

        variables, parameters = self.get_symbols(variable_assignments, parameter_assignments)
        self.create_simulation_variables(variable_assignments, variables | {T}, parameters)
        self.create_simulation_parameters(parameter_assignments, variables | {T}, parameters)
        
        self.variables.update({T: self.time})

    def create_time_variable(self):
        # At the moment the only global variable is time
        self.time = SimVariable(Variable(T, 0.0, "system time"))
        self.time.set_update_rule(
            SimUpdateRule(
                equation="1",
                variables={},
                parameters={},
                description="system time",
            )
        )

    def get_symbols(self, variable_assignments, parameter_assignments):
        variables = {assg.variable.symbol for assg in variable_assignments}
        parameters = {assg.parameter.symbol for assg in parameter_assignments}
        return variables, parameters

    def create_simulation_variables(self, variable_assignments, variables, parameters):
        for assg in variable_assignments:
            update_rule = assg.to_update_rule(variables, parameters)
            sim_variable = SimVariable(assg.variable)
            sim_variable.set_update_rule(update_rule)
            self.variables[assg.variable.symbol] = sim_variable

    def create_simulation_parameters(self, parameter_assignments, variables, parameters):
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
                    raise PopulationSystemError(
                        f"Parameter {parsym} references undefined symbol {dependency}"
                    )
        try:
            nodes = nx.topological_sort(G)
        except nx.exception.NetworkXUnfeasible:
            raise PopulationSystemError(
                f"System parameters contain cyclic dependencies"
            )
        return nodes

    def get_readout(self):
        print_vars_dict = {v: sym.Symbol(f"x_{i}") for i, v in enumerate(self.variables) if v is not T} | {T: sym.Symbol("t")}
        print_pars_dict = {p: sym.Symbol(f"a_{i}") for i, p in enumerate(self.parameters)}
        odes = [var.get_readout(print_vars_dict, print_pars_dict) for var in self.variables.values()]
        functions = [par.get_readout(print_vars_dict, print_pars_dict) for par in self.parameters.values()]
        print(f"system ODEs: \[{self.combine_latex(*odes)}\]")
        print(f"system functions: \[{self.combine_latex(*functions)}\]")
        print(f"variable mappings: {print_vars_dict}")
        print(f"parameter mappings: {print_pars_dict}")

    def combine_latex(self, *equations):
        n = len(equations)
        if n == 0:
            return ""
        l1 = r"\left\{\begin{matrix}%s\end{matrix}\right."
        l2 = r" \\ ".join(eq for eq in equations)
        return l1 % l2
            





class Simulation:
    def __init__(self, system, solver = "discrete_int"):
        self.system = system
        self.variables = system.variables
        self.parameters = system.parameters
        self.time = system.time
        self.solver = solver

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
        update_rule._initialize_dependencies(set(self.variables.keys()), set())
        update_rule._equation_lambdified = None

    def set_initial_values(self, values: dict):
        for var in values:
            try:
                variable = self.variables[var]
            except:
                raise KeyError(f"{var} is not a system variable.")
            variable.time_series = [values[var]]

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
        #self._update_buffer(self.simulation.time)
        for variable in self.simulation.variables.values():
            self._update_buffer(variable)
        for variable in self.simulation.variables.values():
            self._update_time_series(variable, time_step)
        #self._update_time_series(self.simulation.time, time_step)

    def _update_buffer(self, variable):
        variable.buffer = variable.time_series[-1]

    def _update_time_series(self, variable, time_step):
        new_value = self._evaluate_update(variable.update_rule, variable.buffer, time_step)
        variable.time_series.append(new_value)

    def _evaluate_update(self, update_rule, old_value, time_step):
        value = self._evaluate_expression(update_rule)
        return old_value + value*time_step

    def _evaluate_expression(self, update_rule):
        if update_rule._equation_lambdified is None:
            update_rule._lambdify()
        v_args = [self.simulation.variables[v].buffer for v in update_rule.variables]
        p_args = [self.simulation.parameters[p].computed_value for p in update_rule.parameters]
        args = v_args + p_args
        return update_rule._equation_lambdified(*args)

    def _advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                "Number of time steps in a day must be a positive integer, "
                f"not '{n_steps}'."
            )
        for i in range(n_steps):
            self._advance_time(1 / n_steps)

