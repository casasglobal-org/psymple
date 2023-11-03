import sympy as sym
import numpy as np
from collections import defaultdict
#from DegreeDays import DegreeDays, FFTemperature
from functools import reduce
from operator import add

# Create the dictionary passed to sym.sympify and sym.lambdify to convert custom functions
sym_custom_ns = {}
#sym_custom_ns = {'DegreeDays': DegreeDays, 'FFTemperature': FFTemperature}

T = sym.Symbol('T')

'''
Symbol_Wrapper classes
'''

class Symbol_Wrapper:
    def __init__(self, symbol: sym.Symbol, description: str):
        self.symbol = symbol
        self.description = description

    def __str__(self):
        return f"{type(self).__name__} object: {self.description} \n {self.symbol} = {self.contents}"
    
    
class Variable(Symbol_Wrapper):
    def __init__(self, symbol, time_series, description):
        super().__init__(symbol, description)
        self.time_series = time_series

    @classmethod
    def basic(cls, symbol_name, symbol_letter = 'x', time_series = None, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), time_series or [0], description or f"{symbol_name} variable")
    
    @classmethod
    def summary(cls, symbol_name, symbol_letter = 's', contents = None, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), contents, description or f"{symbol_name} summary variable")
    

class Parameter(Symbol_Wrapper):

    def __init__(self, symbol, value, description):
        super().__init__(symbol, description)
        self.value = value

    @classmethod
    def basic(cls, symbol_name, symbol_letter, value, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), value, description or f"{symbol_name} basic parameter")
    
    @classmethod
    def composite(cls, symbol_name, symbol_letter, contents, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), sym.sympify(contents, locals = sym_custom_ns), description or f"{symbol_name} composite parameter")        


'''
Container classes: contain lists of wrapper objects. Contain methods to edit and access these lists.
'''

class Container:
    def __init__(self, objects):
        if objects is None:
            objects = []
        self.objects = objects
        #self.contains_type = Symbol_Wrapper
    
    def __add__(self, other):
        if isinstance(other, type(self)):
            to_add = other.objects
        elif isinstance(other, self.contains_type):
            to_add = [other]
        else:
            raise TypeError(f"Unsupported addition type within {type(self)}.__name__")
        for obj in to_add:
            if self.check_duplicates:
                self._duplicates(self.get_symbols(), obj.symbol)
            self.objects.append(obj)
        return type(self)(self.objects)
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(self.objects[index])
        elif isinstance(index, int):
            return self.objects[index]
        elif isinstance(index, str):
            return getattr(self, index)

    def _duplicates(self, list, object):
        if object in list:
            raise Exception(f"The symbol '{object}' has already been defined. Try a new symbol.")


    def _edit(self, edit_type, index, object = None):
        if edit_type == "remove":
            pass
        elif edit_type == "replace":
            self[index] = object
        elif edit_type == "add":
            self.objects += [object]
    
    def _objectify(self, expr):
        if isinstance(expr, str) or isinstance(expr, sym.Symbol):
            return next(obj for obj in self if obj.symbol == sym.sympify(expr, locals = sym_custom_ns))
        elif isinstance(expr, self.contains_type):
            return expr
        else:
            raise TypeError(f"arguments to _objectify should be of type {repr(str)}, {repr(sym.Symbol)} or {self.contains_type}")
        

   
class Variables(Container):
    def __init__(self, variables: list[Variable] = None):
        super().__init__(variables)
        self.variables = self.objects
        self.contains_type = Variable
        self.check_duplicates = True

    def get_symbols(self):
        return [obj.symbol for obj in self.objects]
    
    def get_time_series(self):
        return [obj.time_series for obj in self.objects]
    
    def get_final_values(self):
        return [obj.time_series[-1] for obj in self.objects]
        

class Parameters(Container):
    def __init__(self, parameters: list[Parameter] = None):
        super().__init__(parameters)
        self.parameters = self.objects
        self.contains_type = (Parameter, Variable)
        self.check_duplicates = True

    def get_symbols(self):
        return [obj.symbol for obj in self.objects]
    
    def get_values(self):
        return [obj.value for obj in self.objects]


class Update_Rules(Container):
    def __init__(self, update_rules: list = None):
        super().__init__(update_rules)
        self.update_rules = self.objects
        self.contains_type = Update_Rule
        self.check_duplicates = False

    def get_equations(self):
        return [u.equation for u in self]
    
    def get_equations_lambdified(self):
        return [u.equation_lambdified for u in self]
    
    def _combine_update_rules(self):
        vars = list(set([u.variable for u in self]))
        new_rules = []
        for var in vars:
            updates_for_var = [u for u in self if u.variable == var]
            new_rules.append(self._combine(var, updates_for_var))
        return Update_Rules(new_rules)

    def _combine(self, variable, update_rules):
        equations = reduce(add, [u.equation for u in update_rules])
        variables = Variables(list(set([v for u in update_rules for v in u.all_variables])))
        parameters = Parameters(list(set([p for u in update_rules for p in u.parameters])))
        return Update_Rule(variable, equations, variables, parameters, f"Combined update rule for variable '{variable.symbol}'" )



class Operators(Container):
    def __init__(self, operators: list = None):
        super().__init__(operators)
        self.operators = self.objects
        self.contains_type = Operator
        self.check_duplicates = False


'''
Equation wrapper clases
TODO: abstract Equation_Wrapper class? Need to see how Operator class develops
'''


class Update_Rule:
    def __init__(self, variable: Variable, equation, all_variables: Variables, parameters: Parameters, description: str):
        self.variable = variable
        self.equation = sym.sympify(equation, locals = sym_custom_ns)
        self.all_variables = all_variables
        self.parameters = parameters
        self.description = description
        self.equation_lambdified = None
        if not variable in all_variables:
            raise Exception(f"The equation variable '{variable.symbol}' must be contained in 'all_variables'")
        self._check_equation_completeness()

    @classmethod
    def add_from_pop(cls, pop, variable: Variable, equation, description = None):
        pop_vars = set(pop.variables.get_symbols())
        pop_params = set(pop.parameters.get_symbols())
        equation_symbols = sym.sympify(equation, locals = sym_custom_ns).free_symbols
        equation_variables = [pop.variables._objectify(symbol) for symbol in equation_symbols.intersection(pop_vars)]
        equation_parameters = [pop.parameters._objectify(symbol) for symbol in equation_symbols.intersection(pop_params)]
        return cls(variable, equation, Variables(equation_variables), Parameters(equation_parameters), description or f"{variable.symbol} update rule")
    

    def __str__(self):
        return f"{self.description}: d[{self.variable.symbol}]/dt = {self.equation} in variables '{self.all_variables.get_symbols()}' and parameters {self.parameters.get_symbols()}"

    def _check_equation_completeness(self):
        variable_symbols = self.all_variables.get_symbols()
        parameter_symbols = self.parameters.get_symbols()
        equation_symbols = self.equation.free_symbols
        difference = equation_symbols - set(variable_symbols + parameter_symbols)
        if difference:
            raise Exception(f"The {'symbol' if len(difference) == 1 else 'symbols'} '{difference}' in equation '{self.equation}' {'does' if len(difference) == 1 else 'do'} not have an associated {Variable.__name__} object.")
    
    def get_variables(self):
        return [v.symbol for v in self.all_variables]
    
    def get_parameters(self):
        return [p.symbol for p in self.parameters]
    

class Operator:
    '''
    An Operator object will define generic update rules for a Variables object, in the same way that an Update_Rule defines
    an update rule for a Variable object.
    '''
    def __init__(self, name, function, description):
        self.name = name
        self.operator = function
        self.description = description

'''
Population classes
'''

class Population:
    def __init__(self, name: str):
        self.name = name
        self.variable = Variable.basic(name, description = f"{name} population variable")
        self.populations = []
        self.windows = []
        self.variables = Variables([self.variable])
        self.parameters = Parameters()
        self.update_rules = Update_Rules()

    def get_population_names(self):
        return [pop.name for pop in self.populations]
    
    def get_window_names(self):
        return [win.name for win in self.windows]

    def _add_population(self, population):
        # Change self.variable to summary variable
        self.populations.append(population)
        self.variables += population.variables
        self.parameters += population.parameters
        self.update_rules += population.update_rules

    def _add_parameter(self, type, symbol_name, symbol_letter, contents, description = None):
        if type == "basic":
            param = Parameter.basic(symbol_name, symbol_letter, contents, description)
        elif type == "composite":
            param = Parameter.composite(symbol_name, symbol_letter, contents, description)
        self.parameters += param
        setattr(self.parameters, symbol_name, param)

    def _add_update_rule(self, variable, equation, description = None):
        update_rule = Update_Rule.add_from_pop(self, self.variables._objectify(variable), equation, description)
        self.update_rules += update_rule

    def _create_window(self, name: str, variables: Variables = None, operators: Operators = None):
        window = Window(name, variables, operators)
        self.windows.append(window)
        setattr(self, name, window)

    def compile(self):
        return System(self)


class Indexed_Population(Population):
    def __init__(self, name: str, shape: tuple):
        super().__init__(name)
        self.array = np.empty(shape, dtype = object)

    def __getitem__(self, index):
        return self.array[index]
    
    def add_population(self, population, index):
        super()._add_population(population)
        self.array[index] = population
        



'''
Window classes
'''


class Window:
    def __init__(self, name: str, variables: Variables = Variables(), operators: Operators = Operators()):
        self.name = name
        self.variables = variables
        self.operators = operators

    def _add_operator(self, name, function, description = None):
        operator = Operator(name, function, description or f"{self.name} operator: {name}")
        self.operators += operator
        setattr(self, name, operator)


'''
System
'''

class System:
    def __init__(self, population):
        self.population = population
        self.system_time = Variable(T, [0], "system time")
        self.system_variables = Variables([self.system_time])
        self.variables = self.population.variables + self.system_variables
        self.parameters = self.population.parameters
        self.update_rules = self.population.update_rules._combine_update_rules()
        self._compute_parameter_graph()
        self._compute_parameters()
        self._lambify_update_rules()

    def _compute_parameter_graph(self):
        pass

    def _compute_parameters(self):
        sub_values = zip(self.parameters.get_symbols(), self.parameters.get_values())
        return sub_values
    
    def _lambify_update_rules(self):
        for u in self.update_rules:
            u.equation_lambdified = sym.lambdify([u.all_variables.get_symbols() + self.system_variables.get_symbols()], u.equation)

    def advance_time(self, time_step):
        for v in self.variables:
            v.buffer = v.time_series[-1]
        for u in self.update_rules:
            u.variable.time_series.append(u.variable.buffer + time_step * u.equation_lambdified([v.buffer for v in u.all_variables] + [v.buffer for v in self.system_variables] ))
        self.system_time.time_series.append(self.system_time.time_series[-1] + time_step)

    def advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(f"Number of time steps in a day must be a positive integer, not '{n_steps}'.")
        for i in range(n_steps):
            self.advance_time(1/n_steps)

    def simulate(self, t_end, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(f"Simulation time must terminate at a positive integer, not '{n_steps}'.")
        for i in range(t_end):
            self.advance_time_unit(n_steps)



        









    


    

