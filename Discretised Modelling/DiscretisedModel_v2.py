import sympy as sym

class Parameter:
    def __init__(self, name, symbol_name=None, value=None):
        '''
        Args:
            name (string):
            symbol_name (string):
            value: A numerical value or a sympy expression that may contain a
                time variable T (and maybe spatial information in the future?)
        '''
        self.name = name
        self.symbol = sym.Symbol(symbol_name or name)
        self.value = value

class Variable:

    def __init__(self, name: str, symbol_name: str, values_vector: list, new_values_vector = None):
        '''
        Stores information about a system variable. 
        TODO: new_values_vector to be used for double-buffering (not implemented)
        '''
        self.name = name
        self.initial_value = values_vector[0]
        self.symbol = sym.Symbol(symbol_name)
        self.values_vector = values_vector

class Expression:

    def __init__(self, name, population, equation, other_variables: list = [], parameters: list = []):
        '''
        An expression object contains an equation which will be updated at each model time step. For the equation
        dy/dt = f(t,y):
        Args:
            name (string)
            population (population object): population to update, ie. population.variable = y
            equation (SymPy expression): f(t,y)
            other_variables (list of variable objects): other system variables appearing in f(t,y)
            parameters (list of parameter objects): all parameters appearing in f(t,y)
            
        '''
        self.name = name
        self.population = population
        self.equation = equation
        self.other_variables = other_variables
        self.parameters = parameters


class Operator:

    def __init__(self, expression, sub_time_step, update_type: str = "add"):
        '''
        Advances a given difference equation with the given parameters

        rate_method not implemented: will provide option to use eg. Runge-Kutta rather than current (very bad) Euler method

        TODO: Caching to stop recompiles every time
        TODO: Allow for multiplication updates as well as linear (potentially with multiple time steps too)
        '''
        self.population = expression.population
        self.equation = expression.equation
        self.other_variables = expression.other_variables
        self.parameters = expression.parameters
        self.equation_variables = self.other_variables + [self.population.variable]
        self.sub_equation()
        self.lambdify_equation()
        self.advance(update_type, sub_time_step)

    def sub_equation(self):
        params_for_sub = [(p.symbol, p.value) for p in self.parameters]
        self.equation_subbed = self.equation.subs(params_for_sub)
        #print(self.equation_subbed)
    
    def lambdify_equation(self):
        equation_variables_symbols = [v.symbol for v in self.equation_variables]
        self.equation_lambdified = sym.lambdify(equation_variables_symbols,self.equation_subbed)

    def advance(self, update_type, sub_time_step):
        if update_type == "add":
            values = [v.values_vector[-1] for v in self.equation_variables]
            update_vector = self.population.variable.values_vector
            step_increment = 1/sub_time_step * self.equation_lambdified(*values)
            update_vector.append(update_vector[-1] + step_increment)


class System:
    '''
    A system class takes the population class to be run, eventually along with run data (run length, season dates,...) and also
    an (ordered) list of expressions, which is passed to an operator object to execute at each time step.
    '''
    def __init__(self, name: str, population, updates: list, time_step: int = 1):
        self.name = name
        self.population = population
        self.updates = updates
        self.time_step = time_step

    def change_updates(self, updates: list):
        self.updates = updates

    def change_time_step(self, time_step: int):
        self.time_step = time_step

    def advance_time(self, sub_time_step, expression):
        Operator(expression, sub_time_step, "add")

    def update(self, sub_time_step):
        for i in range(sub_time_step):
            for j in range(len(self.updates)):
                self.advance_time(sub_time_step, self.updates[j])



class Population:
    def __init__(self, name: str):
        self.name = name
        self.populations = []
        self.variables = []
        self.parameters = []
        self.expressions = []

    def get_variables(self):
        return [(v.name, v.symbol, v.initial_value, v.values_vector) for v in self.variables]
    
    def get_parameters(self):
        return [(p.name, p.symbol, p.value) for p in self.parameters]
    
    def _add_components(self, parameters: list, expressions: list):
        self.parameters += parameters
        self.expressions += expressions
    
    def refresh_components(self):
        self.variables = [v for s in self.populations for v in s.variables]
        self.parameters = [p for s in self.populations for p in s.parameters]
        self.expressions = [e for s in self.populations for e in s.expressions]
    
    def set_initial_value(self, population, initial_value: float):
        population.variable.values_vector[0] = initial_value

    def add_population(self, population):
        for p in population.populations:
            self.populations.append(p)
            self.refresh_components()

    def add_growth_rate(self, population, rate):
        '''
        TODO: generalise into add_equation function. Add parameter consistency checking.
        '''
        p = population
        p.growth_rate = Parameter(f"{p.name} growth_rate", f"r_{p.name}", rate)
        p.growth = Expression(f"{p.name} growth", p, p.growth_rate.symbol * p.variable.symbol,[],[p.growth_rate])
        p._add_components([p.growth_rate],[p.growth])
        self.refresh_components()

    def link_populations(self, population, previous_population, rate):
        p = population
        q = previous_population
        p.link_rate = Parameter(f"{q.name} to {p.name} transfer rate", f"k_[{q.name} -> {p.name}]", rate)
        p.delay = Expression(f"{q.name} to {p.name} delay", p, p.link_rate.symbol * (q.variable.symbol - p.variable.symbol), [q.variable], [p.link_rate])
        p._add_components([p.link_rate],[p.delay])
        self.refresh_components()


class DDTM(Population):
    
    def __init__(self, name, k_bins: int, del_rate: float, DD_func):
        super().__init__(name)
        self.k_bins = k_bins
        self.transfer_rate = (k_bins * DD_func) / del_rate
        self.create_bins()
        self.link_cohorts()

    def create_bins(self):
        for i in range(self.k_bins):
            self.add_population(Base_Population(f"{self.name}_{i}"))

    def link_cohorts(self):
        self.first().add_growth_rate(- self.transfer_rate)
        for i in range(1,self.k_bins):
            self.link_populations(self.populations[i], self.populations[i-1], self.transfer_rate)

    def first(self):
        return self.populations[0]   
    
    def last(self):
        return self.populations[-1]
    




class Base_Population(Population):
    '''
    A base population is a Population object together with a Variable object which is simulated by the whole system. 
    Provides utility functions to update initial values, growth rate etc from self rather than from population object.
    '''
    def __init__(self, name: str, initial_value: float = 0):
        super().__init__(name)
        self.variable = Variable(f"{name} variable",f"x_{name}",[initial_value])
        self.variables.append(self.variable)
        self.populations.append(self)

    def set_initial_value(self, initial_value: float):
        super().set_initial_value(self, initial_value)

    def add_growth_rate(self, rate):
        super().add_growth_rate(self, rate)

