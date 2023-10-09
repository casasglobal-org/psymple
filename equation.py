import sympy as sym

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
        self.parameters = []
        self.dependent_variables = []

    def set_initial_value(self, initial_value):
        self.initial_value = initial_value

    def get_subbed_ode(self):
        params = [(p.symbol, p.value) for p in self.parameters]
        return self.ODE.subs(params)

    def get_variable(self):
        return Variable(self.name, self.var_symbol, self.initial_value)

    def update_ode(self, expression, parameters=[], dependent_variables=[]):
        '''
        Args:
            expression: a sympy expression
        '''
        
        # TODO: extract parameters and dependent variables automatically?
        # Or verify that parameters and dependent variables are complete?
        self.ODE += expression
        self.parameters += parameters
        self.dependent_variables += dependent_variables


class Unit(Equation):
    '''
    TODO: Document this class. Is Unit the right name?
    '''

    def __init__(self, name, initial_value=0, var_name=None, growth_rate=0, capacity=None):
        super().__init__(name, initial_value, var_name)
        self.add_growth_rate(growth_rate)
        self.add_capacity(capacity)

    def add_growth_rate(self, rate: float):
        # TODO: ensure there's no parameter duplication here.
        self.growth_rate = Parameter(f"{self.name} growth rate", f"r_{self.name}", rate)
        self.update_ode(self.growth_rate.symbol * self.var_symbol, [self.growth_rate])

    def add_capacity(self, capacity: float):
        # TODO: ensure there's no parameter duplication here.
        if capacity is None:
            return
        self.capacity = Parameter(f"{self.name} capacity", f"K_{self.name}", capacity)
        self.update_ode(-self.var_symbol**2 * self.growth_rate.symbol / self.capacity.symbol, [self.capacity])


class Parameter:
    def __init__(self, name, symbol_name=None, value=None):
        self.name = name
        self.symbol = sym.Symbol(symbol_name or name)
        self.value = value


class Variable:
    def __init__(self, name, symbol, initial_value):
        self.name = name
        self.initial_value = initial_value
        self.symbol = symbol
