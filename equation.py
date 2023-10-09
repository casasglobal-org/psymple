import sympy as sym
from parameters import Parameter, Variable

class Equation:

    def __init__(self, name, initial_value=0, var_name=None):
        '''
        An equation (ODE), usually part of a system.
        Each equation corresponds to a variable.

        Args:
            name
            var_name
            initial_value
        '''
        self.name = name
        # TODO: store this as symbol or as string?
        self.var_symbol = sym.Symbol(var_name or f"x_{name}")
        self.initial_value = initial_value
        self.ODE = sym.core.numbers.Zero()
        # TODO: Should this be a list or name indexed dict?
        self.parameters = {}
        # A set of symbols
        self.dependent_symbols = set()

    def set_initial_value(self, initial_value):
        self.initial_value = initial_value

    def get_parameters(self):
        return self.parameters

    def get_dependent_symbols(self):
        return self.dependent_symbols

    def get_variable(self):
        return Variable(self.name, self.var_symbol, self.initial_value)

    def get_ode(self):
        return self.ODE

    def update_ode(self, expression, parameters=[]):
        '''
        Add an expression to the ODE.

        A list of parameters has to be provided. Dependent variables
        are automatically collected. Everything that is not declared
        as a parameter is considered a variable.

        Args:
            expression: a sympy expression
                This expression is added to the RHS of the ODE
            parameters: a list of parameters that are part of the expression
        '''

        self.ODE += expression
        Parameter.reconcile_parameters(self.parameters, parameters)
        symbols = expression.free_symbols - {p.symbol for p in self.parameters.values()} - {self.var_symbol}
        self.dependent_symbols |= symbols


class Unit(Equation):
    '''
    TODO: Document this class. Is Unit the right name?
    '''

    def __init__(self, name, initial_value=0, var_name=None, growth_rate=None, capacity=None):
        super().__init__(name, initial_value, var_name)
        self.add_growth_rate(growth_rate)
        self.add_capacity(capacity)

    def add_growth_rate(self, rate: float):
        # TODO: ensure there's no parameter duplication here.
        if rate is None:
            return
        self.growth_rate = Parameter(f"{self.name} growth rate", f"r_{self.name}", rate)
        self.update_ode(self.growth_rate.symbol * self.var_symbol, [self.growth_rate])

    def add_capacity(self, capacity: float):
        # TODO: ensure there's no parameter duplication here.
        if capacity is None:
            return
        self.capacity = Parameter(f"{self.name} capacity", f"K_{self.name}", capacity)
        self.update_ode(-self.var_symbol**2 * self.growth_rate.symbol / self.capacity.symbol, [self.capacity])

