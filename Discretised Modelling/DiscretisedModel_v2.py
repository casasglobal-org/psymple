import sympy as sym
from DegreeDays import *
import itertools as it
import copy

T = sym.Symbol('T') 

class Parameter:
    def __init__(self, name, symbol_name = None, value = None):
        '''
        A Parameter object stores the name, symbol and value of a system parameter.

        Args:
            name (string):
            symbol_name (string):
            value: A numerical value or a SymPy expression that may contain a
                time variable T (and maybe spatial information in the future?)
        '''
        self.name = name
        self.symbol = sym.Symbol(symbol_name or name)
        self.value = value
    
    def sub(self, new_name = None, new_symbol = None, append_name = None):
        new_name = new_name or f"{self.name}_({append_name})"
        new_symbol = new_symbol or f"{str(self.symbol)}_({append_name})"
        return Parameter(new_name, new_symbol, self.value)


class Variable:
    '''
    TODO: Store summary variables as deep SymPy equivalent expressions
    '''
    def __init__(self, name: str, symbol, content, values_vector: list):
        '''
        A Variable object stores the name, symbol and time series of a system variable. There are two subclasses. Variable.base is
        a variable which is simulated by the system. Variable.summary is a variable constructed in terms of base variables, for example
        a sum.

        Args:
            name (string)
            symbol (string)
            content (list): a list of variables on which the value of self depends.
            values_vector (list): initial values stored before a simulation is run.
        '''
        self.name = name
        self.symbol = sym.Symbol(symbol)
        self.content = content
        self.values_vector = values_vector
        self.initial_value = values_vector[0]

    @classmethod
    def base(cls, name, symbol, values_vector):
        return cls(name, symbol, None, values_vector)

    @classmethod
    def summary(cls, name, symbol, content_variables, summary_type):
        if summary_type == "sum":
            summary_func = lambda x: np.sum(x, axis = 0)
        return cls(name, symbol, summary_func([v.symbol for v in content_variables]), summary_func(np.array([v.values_vector for v in content_variables])))

    def sub(self, new_name = None, append_name = None):
        if new_name == None and append_name == None:
            return self
        new_name = new_name or f"{self.name}_({append_name})"
        return Variable(new_name, f"x_{new_name}", self.content, self.values_vector)   
     

class Expression:

    def __init__(self, name, population, equation, other_variables: list = [], parameters: list = []):
        '''
        An expression object contains an equation which will be updated at each model time step. For the equation
        dy/dt = f(t,y), arguments are:

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

    def sub(self, new_pop, vars_sub_list, new_name = None, append_name = None,):
        new_name = new_name or f"{self.name}_({append_name})"
        sub_list = vars_sub_list
        return Expression(new_name, new_pop, self.equation.subs(sub_list), [v.symbol.subs(vars_sub_list) for v in self.other_variables], self.parameters)




class Population:
    def __init__(self, name: str, initial_value: float = 0, variable = None):
        print(f"INIT POP {name}")
        self.name = name
        self.populations = []
        self.populations_flat = []
        self.variables = []
        self.parameters = []
        self.expressions = []
        self.variable = variable or Variable.base(f"{name}", f"x_{name}", [initial_value])
        self.variables.append(self.variable)
        self.populations.append(self)
        self.populations_flat.append(self)

    def sub(self, new_name = None, append_name = None, variable = None):
        new_name = new_name or f"{self.name}_({append_name})"
        return Population(new_name, self.variable.initial_value, variable)

    def get_variables(self):
        return [(v.name, v.symbol, v.initial_value, v.values_vector) for v in self.variables]
    
    def get_parameters(self):
        return [(p.name, p.symbol, p.value) for p in self.parameters]
    
    def get_population_names(self):
        return [p.name for p in self.populations]
    
    def _add_components(self, parameters: list, expressions: list):
        self.parameters += parameters
        self.expressions += expressions
    
    def refresh_components(self):
        self.variables = [v for s in self.populations_flat for v in s.variables]
        self.parameters = [p for s in self.populations_flat for p in s.parameters]
        self.expressions = [e for s in self.populations_flat for e in s.expressions]
    
    def set_initial_value(self, population, initial_value: float):
        population.variable.values_vector[0] = initial_value

    def add_population(self, population):
        self.populations.append(population)
        setattr(self, population.name, population)
        for p in population.populations:
            self.populations_flat.append(p)
        #self.refresh_components()

    def remove_population(self, population):
        for p in population.populations:
            self.populations.remove(p)
            self.refresh_components()

    def add_parameter(self, population, parameter_name, symbol, rate, description = None):
        p = population
        param = Parameter(f"{p.name}: {description or parameter_name}", symbol, rate)
        setattr(p, parameter_name, param)
        p._add_components([param], [])
        self.refresh_components()

    def add_expression(self, population, expression_name, equation, other_variables, parameters, description = None):
        p = population
        expr = Expression(f"{p.name} {description or expression_name}", p, equation, other_variables, parameters)
        setattr(p, expression_name, expr)
        p._add_components([],[expr])
        self.refresh_components()

    def add_growth_rate(self, population, rate):
        '''
        TODO: generalise into add_equation function. Add parameter consistency checking.
        '''
        p = population
        p.add_parameter(p, "growth_rate", "r", rate)
        p.add_expression(p, "growth", p.growth_rate.symbol * p.variable.symbol, [], [p.growth_rate])
        self.refresh_components()

    def link_populations(self, populations, rates):
        '''
        TODO: Buffering not dealt with correctly
        '''
        if len(populations) - 1 != len(rates):
            raise Exception(f"Number of rates in {rates} should be 1 less than number of popultions in {populations}")
        for i in range(len(populations) - 1):
            p = populations[i]
            q = populations[i+1]
            p.add_parameter(p, "flow_rate", f"k_[{self.name}: {p.name} -> {q.name}]", rates[i], f"{p.name} to {q.name} flow rate")
            p.add_expression(p, "flow_out", - p.flow_rate.symbol * p.variable.symbol, [], [p.flow_rate], f"{p.name} to {q.name} flow out")
            if hasattr(self, "flow_in"):
                self.flow_in.expressions = []
        for i in range(1,len(populations)):
            p = populations[i]
            q = populations[i-1]
            p.add_expression(p, "flow_in", q.flow_rate.symbol * q.variable.symbol, [q.variable], [q.flow_rate], f"{q.name} to {p.name} flow in")
        self.refresh_components()



class Age_Structured_Population(Population):
    '''
    TODO: Class method? ie. call Age_Structured_Population.DDTM()
    '''    
    def __init__(self, name, type = None, parameters = None, link = True):
        '''
        Args:
            type: eg. "DDTM". If None or not recognised, empty Population object is created
            parameters: a valid parametrisation of the chosen type

        Parameters for DDTM:
            [k_bins, del_rate, base_temp, DD_func, flow_in_buffer, flow_out_buffer]
        '''
        super().__init__(name)
        print("INIT DDTM")
        self.rates = []
        self.populations = []
        self.populations_flat = []
        if type == "DDTM":
            self.parameters = parameters
            k_bins, del_rate, base_temp, DD_func, flow_in_buffer, flow_out_buffer = parameters
            self.create_bins(k_bins, del_rate, base_temp, DD_func, flow_in_buffer, flow_out_buffer)
            if link:
                self.link_populations(self.populations, self.rates)
            self.variable = Variable.summary(f"{name} summary variable", f"s_{name}", [p.variable for p in self.populations], "sum")

    def create_bins(self, k_bins, del_rate, base_temp, DD_func, flow_in_buffer, flow_out_buffer):
        '''
        TODO: This creates a flow out of self.flow_in.
        '''
        if flow_in_buffer:
            self.flow_in = Population(f"({self.name})_(flow_in)")
            self.add_population(self.flow_in)    
            self.rates.append(k_bins / del_rate)    
        for i in range(k_bins):
            self.add_population(Population(f"({self.name})_({i+1})"))
            self.rates.append(k_bins * DD_func(T, base_temp) / del_rate)
        self.first = self.populations[0]
        self.last = self.populations[k_bins - 1]
        if flow_out_buffer:
            self.flow_out = Population(f"({self.name})_(flow_out)")
            self.add_population(self.flow_out)
        else:
            self.rates.pop(-1)




class Stage_Structured_Population(Population):
    def __init__(self, name):
        super().__init__(name)
        self.rates = []
        self.populations = []
        self.populations_flat = []

    def add_stages(self, populations, rates):
        '''
        TODO: Needs to be split into two functions?
        '''
        if len(populations) - 1 != len(rates):
            raise Exception(f"Number of rates in {rates} should be 1 less than number of popultions in {populations}")
        for p in populations:
            self.add_population(p)
            if hasattr(p, "flow_in"):
                p.inflow = [p.flow_in, "replace"]
            elif hasattr(p, "first"):
                p.inflow = [p.first, "add"]
            else:
                p.inflow = [p, "add"]
            if hasattr(p, "flow_out"):
                p.outflow = [p.flow_out, "replace"]
            elif hasattr(p, "last"):
                p.outflow = [p.last, "add"]
            else:
                p.outflow = [p, "add"] 
        for i in range(len(populations) - 1):
            p = populations[i]
            q = populations[i+1]
            if p.outflow[1] == "add" and q.inflow[1] == "add":
                self.link_populations([p.outflow[0], q.inflow[0]], [rates[i]])
                p.refresh_components()
                q.refresh_components()
            elif p.outflow[1] == "replace" and q.inflow[1] == "replace":
                q.inflow = p.outflow
            else:
                raise Exception(f"The outflow of {p.name} is not compatible with the inflow of {q.name}")
        self.variable = Variable.summary(f"{self.name} summary variable", f"s_{self.name}", [p.variable for p in self.populations], "sum")
        self.refresh_components()

class Multi_Species_Population(Population):

    def __init__(self, name):
        super().__init__(name)

    def add_delay_interaction(self, populations):
        sizes = [len(p.populations_flat) for p in populations]
        coords = list(it.product(*[list(range(s)) for s in sizes]))
        Array = np.empty(sizes, dtype = object)
        for c in list(coords):
            Array[c] = Population("_*_".join([populations[pos].populations_flat[num].name for pos,num in enumerate(c) ]))
            #Array[c] = Variable.base()
            self.add_population(Array[c])
        for c in list(coords):
            c_copy = copy.copy(c)
            sub_vars = []
            for i in range(len(c)):
                for j in range(sizes[i]):
                    c = list(c)
                    c[i] = j
                    c = tuple(c)
                    sub_vars.append([populations[i].populations[j].variable.symbol, Array[c].variable.symbol])
                    c = c_copy
            Array[c].expressions = [e.sub(Array[c], sub_vars, new_name = "new") for pos,num in enumerate(c) for e in populations[pos].populations_flat[num].expressions]
            Array[c].refresh_components()
        self.refresh_components()






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
        self.day = float(1)

    def change_updates(self, updates: list):
        self.updates = updates

    def change_time_step(self, time_step: int):
        self.time_step = time_step

    def advance_time(self, current_day, sub_time_step, expression):
        Operator(expression, current_day, sub_time_step, "add")

    def update(self, sub_time_step):
        for i in range(sub_time_step):
            for j in range(len(self.updates)):
                self.advance_time(self.day, sub_time_step, self.updates[j])
        self.day += 1
        #print(self.day)

class Operator:

    def __init__(self, expression, current_day, sub_time_step, update_type: str = "add"):
        '''
        Advances a given difference equation with the given parameters

        rate_method not implemented: will provide option to use eg. Runge-Kutta rather than current forward Euler method

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
        self.advance(update_type, current_day, sub_time_step)

    def sub_equation(self):
        params_for_sub = [(p.symbol, p.value) for p in self.parameters]
        self.equation_subbed = self.equation.subs(params_for_sub)
        #print(self.equation_subbed)
    
    def lambdify_equation(self):
        equation_variables_symbols = [v.symbol for v in self.equation_variables]
        #print(equation_variables_symbols)
        self.equation_lambdified = sym.lambdify([T,equation_variables_symbols],self.equation_subbed, [{'DegreeDays': DegreeDays}, 'scipy', 'numpy'])

    def advance(self, update_type, current_day, sub_time_step):
        values = [v.values_vector[-1] for v in self.equation_variables]
        update_vector = self.population.variable.values_vector
        if update_type == "add":
            step_increment = 1/sub_time_step * self.equation_lambdified(current_day + 1/sub_time_step, values)
            update_vector.append(update_vector[-1] + step_increment)
        if update_type == "mult":
            update_vector.append(self.equation_lambdified(*values))
