import sympy as sym
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import numpy as np

# This should be moved to a separate file
from equation import Parameter

class System:
    '''
    A self-contained system of ODEs, i.e., its ODE do not contain variables
    that are not part of the system.
    '''
    T = sym.Symbol('T')

    def __init__(self,name: str):
        self.name = name
        self.equations = []
        self.systems = []
        # self.vars = []
        # self.params = {}
        # self.n_systems = 0
        self.needs_compiling = True
        self.lambdified = []

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
        '''check that the ODEs don't contain external variables'''
        raise NotImplementedError()

    def _compile(self):
        '''collect all ODEs and their variables & parameters (recursively)'''
        if not self.needs_compiling:
            return
        self.needs_compiling = False
        self.lambdified, self.variables = self._get_compiled()

    def _get_compiled_equations(self):
        subbed_odes = []
        variables = []
        for equation in self.equations:
            subbed_odes.append(equation.get_subbed_ode())
            variables.append(equation.get_variable())

        variable_symbols = [v.symbol for v in variables]
        # lambdify:
        # Takes a list of sympy symbols, and a sympy expression
        # This could possibly be optimized to only include the variables present in the ode
        # We could provide a method that compiles the lambdification of a system,
        # and only then put all the ODEs of the lambdification together.
        # We may have parameters in the future that are shared across multiple equations.
        # Then it would make sense to collect and only sub in parameters at the end.
        lambdified = [sym.lambdify([System.T, variable_symbols], ode) for ode in subbed_odes]
        return lambdified, variables

    def _get_compiled(self):
        lambdified, variables = self._get_compiled_equations()
        for system in self.systems:
            l, v = system._get_compiled()
            lambdified += l
            variables += v
        return lambdified, variables

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
        param12 = Parameter(f"c_[{unit1.name} -> {unit2.name}]", value=rate12)
        param21 = Parameter(f"c_[{unit2.name} -> {unit1.name}]", value=rate21)
        unit1.update_ode(param12.symbol * unit1.var_symbol * unit2.var_symbol, parameters=[param12], dependent_variables=[unit2.var_symbol])
        unit2.update_ode(param21.symbol * unit1.var_symbol * unit2.var_symbol, parameters=[param21], dependent_variables=[unit1.var_symbol])


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
