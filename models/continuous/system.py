import sympy as sym
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import numpy as np

# This should be moved to a separate file
from parameters import Parameter
from equation import Unit

class System:
    '''
    A self-contained system of ODEs, i.e., its ODE do not contain variables
    that are not part of the system.
    '''
    T = sym.Symbol('T')

    def __init__(self, name: str):
        self.name = name
        self.equations = []
        self.systems = []
        self.parameters = {}
        self.explicit_parameters = {}
        # TODO: This is not updated if a dependent system or
        # ODE is changed without the knowledge of this system.
        self.needs_compiling = True
        self.lambdified = []
        self.variables = []

    def add_system(self, system):
        # Note: if a subsystem gets updated, we won't know about it,
        # and no recompilation will be triggered.
        # This can lead to unexpected behavior, so we should
        # maybe store a deep copy of the system/equation.
        self.needs_compiling = True
        self.systems.append(system)

    def add_equation(self, equation):
        self.needs_compiling = True
        self.equations.append(equation)

    def _validate(self):
        '''
        Check that the ODEs don't contain external variables
        and all parameters are initialized.
        '''
        # TODO: Check for external variables.
        for param in self.parameters.values():
            if param.value is None:
                raise ValueError(f"Parameter '{param.name}' is not initialized.")

    def set_parameter_value(self, name, value):
        self.explicit_parameters[name] = Parameter(name, value=value)

    def get_parameters(self):
        self._cache_parameters()
        return self.parameters

    def get_equations(self):
        equations = []
        for system in self.systems:
            equations += system.get_equations()
        equations += self.equations
        return equations

    def _cache_parameters(self):
        # TODO: We may try to optimize this later so this is only
        # recomputed whenever necessary.
        for equation in self.equations:
            Parameter.reconcile_parameters(self.parameters, equation.get_parameters().values())
        for system in self.systems:
            Parameter.reconcile_parameters(self.parameters, system.get_parameters().values())
        Parameter.reconcile_parameters(self.parameters, self.explicit_parameters, warn=True)

    def _get_compiled(self):
        self._cache_parameters()
        self._validate()
        equations = self.get_equations()
        params = [(p.symbol, p.value) for p in self.get_parameters().values()]
        # Get the ODES and substitute in the parameters
        odes = [e.get_ode() for e in equations]
        odes = [ode.subs(params) for ode in odes]
        # TODO: We may want to provide a method that returns
        # the list of odes/substituted odes (see above) without solving
        variables = [e.get_variable() for e in equations]
        variable_symbols = [v.symbol for v in variables]

        # lambdify:
        # Takes a list of sympy symbols, and a sympy expression
        # This could possibly be optimized to only include the variables present in the ode
        # We could provide a method that compiles the lambdification of a system,
        # and only then put all the ODEs of the lambdification together.
        # We may have parameters in the future that are shared across multiple equations.
        # Then it would make sense to collect and only sub in parameters at the end.
        lambdified = [sym.lambdify([System.T, variable_symbols], ode) for ode in odes]
        return lambdified, variables

    def _compile(self):
        '''collect all ODEs and their variables & parameters (recursively)'''
        if not self.needs_compiling:
            return
        self.needs_compiling = False
        self.lambdified, self.variables = self._get_compiled()

    def ODE_constructor(self, t, y):
        self._compile()
        return [f(t, y) for f in self.lambdified]

    def solve(self, t_range):
        self._compile()
        y0 = [v.initial_value for v in self.variables]
        ivp_solution = solve_ivp(self.ODE_constructor, t_range, y0, dense_output=True)
        return Solution(ivp_solution, self.variables, t_range)
        # TODO: return value


class Population(System):
    def __init__(self, name):
        super().__init__(name)

    def add_interaction(self, unit1, unit2, rate12, rate21):
        # This could be static method, as we're not referencing self
        # Maybe we will want to reference self to update the parameter list or something in the future
        param12 = Parameter(f"{unit1.name} to {unit2.name} rate", f"c_[{unit1.name} -> {unit2.name}]", value=rate12)
        param21 = Parameter(f"{unit2.name} to {unit1.name} rate", f"c_[{unit2.name} -> {unit1.name}]", value=rate21)
        unit1.update_ode(param12.symbol * unit1.var_symbol * unit2.var_symbol, parameters=[param12])
        unit2.update_ode(param21.symbol * unit1.var_symbol * unit2.var_symbol, parameters=[param21])
        self.needs_compiling = True

    def link_lifestage(self, unit1, unit2, rate12):
        # This could be static method, as we're not referencing self
        param12 = Parameter(f"{unit1.name} -> {unit2.name} transfer rate", f"k_[{unit1.name} -> {unit2.name}]", value=rate12)
        unit2.update_ode(param12.symbol * (unit1.var_symbol - unit2.var_symbol), parameters=[param12])
        self.needs_compiling = True


class Cohort(Population):
    def __init__(self, name, n_buckets):
        super().__init__(name)
        for i in range(n_buckets):
            self.add_equation(Unit(f"{name}_{i}"))

    def last(self):
        return self.equations[-1]

    def first(self):
        return self.equations[0]

    def link_units(self, rate):
        # We may also support a list of rates in the future.
        for i in range(len(self.equations)-1):
            self.link_lifestage(self.equations[i], self.equations[i+1], rate)


class Solution:
    def __init__(self, ivp_solution, variables, t_range):
        self.ivp_solution = ivp_solution
        self.variables = variables
        self.t_range = t_range

    def plot(self):
        # TODO
        t = np.linspace(self.t_range[0], self.t_range[1], 1001)
        plt.plot(t, self.ivp_solution.sol(t).T)
        plt.legend([v.name for v in self.variables], loc='best')
        plt.xlabel('t')
        plt.grid()
        plt.show()

    def as_dict(self):
        # TODO
        # mapping variables to time-series vectors
        raise NotImplementedError()

    def get_vector(self, variable_name):
        # TODO
        # time-series vector for the variable
        raise NotImplementedError()
