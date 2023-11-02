import sympy as sym
import numpy as np
from collections import defaultdict

T = sym.Symbol('T')

'''
Symbol_Wrapper classes
'''

class Symbol_Wrapper:
    def __init__(self, symbol: sym.Symbol, contents, description: str):
        self.symbol = symbol
        self.contents = contents
        self.description = description

    def __str__(self):
        return f"{type(self).__name__} object: {self.description} \n {self.symbol} = {self.contents}"
    
    
class Variable(Symbol_Wrapper):

    @classmethod
    def basic(cls, symbol_name, symbol_letter = 'x', time_series = [0], description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), time_series, description or f"{symbol_name} variable")
    
    @classmethod
    def summary(cls, symbol_name, symbol_letter = 's', contents = None, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), contents, description or f"{symbol_name} summary variable")
    

class Parameter(Symbol_Wrapper):

    @classmethod
    def basic(cls, symbol_name, symbol_letter, value, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), value, description or f"{symbol_name} basic parameter")
    
    @classmethod
    def composite(cls, symbol_name, symbol_letter, contents, description = None):
        return cls(sym.Symbol(f"{symbol_letter}_{symbol_name}"), sym.sympify(contents), description or f"{symbol_name} composite parameter")        


'''
Equation wrapper clases
TODO: abstract Equation_Wrapper class? Need to see how Operator class develops
'''


class Update_Rule:
    def __init__(self, variable, equation, all_variables, parameters, description):
        self.variable = variable
        self.equation = equation
        self.all_variables = all_variables
        self.parameters = parameters
        self.description = description

    @classmethod
    def add_from_pop(cls, pop, variable, equation, description = None):
        pop_vars = set(pop.variables.get_symbols() + [variable.symbol])
        pop_params = set(pop.parameters.get_symbols())
        equation_symbols = equation.free_symbols
        equation_variables = [pop.variables._objectify(symbol) for symbol in equation_symbols.intersection(pop_vars)]
        equation_parameters = [pop.parameters._objectify(symbol) for symbol in equation_symbols.intersection(pop_params)]
        return cls(variable, equation, equation_variables, equation_parameters, description or f"{variable.symbol} update rule")
    
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
Container classes: contain lists of wrapper objects. Contain methods to edit and access these lists.
'''

class Container:
    def __init__(self, objects):
        self.objects = objects
        #self.contains_type = Symbol_Wrapper
    
    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)(self.objects + other.objects)
        elif isinstance(other, self.contains_type):
            return type(self)(self.objects + [other])
        else:
            raise TypeError(f"Unsupported adddition type within {type(self)}")
        
    def _edit(self, edit_type, index, object = None):
        if edit_type == "remove":
            pass
        elif edit_type == "replace":
            self[index] = object
        elif edit_type == "add":
            self.objects += [object]
        
    def __getitem__(self, index):
        if isinstance(index, int):
            return self.objects[index]
        elif isinstance(index, str):
            return getattr(self, index)
    
    def _objectify(self, expr):
        if isinstance(expr, str) or isinstance(expr, sym.Symbol):
            return next(obj for obj in self if obj.symbol == sym.sympify(expr))
        elif isinstance(expr, self.contains_type):
            return expr
        else:
            raise TypeError(f"arguments to _objectify should be of type str, sym.Symbol or {self.contains_type}")
        
    def get_symbols(self):
        return [obj.symbol for obj in self.objects]
    
    def get_contents(self):
        return [obj.contents for obj in self.objects]

   
class Variables(Container):
    def __init__(self, variables: list = []):
        super().__init__(variables)
        self.variables = self.objects
        self.contains_type = Variable
        

class Parameters(Container):
    def __init__(self, parameters: list = []):
        super().__init__(parameters)
        self.parameters = self.objects
        self.contains_type = (Parameter, Variable)


class Update_Rules(Container):
    def __init__(self, update_rules: list = []):
        super().__init__(update_rules)
        self.update_rules = self.objects
        self.contains_type = Update_Rule

    def get_equations(self):
        return [u.equation for u in self.update_rules]
    
    def _combine_update_rules(self):
        pass


class Operators(Container):
    def __init__(self, operators: list = []):
        super().__init__(operators)
        self.operators = self.objects
        self.contains_type = Operator




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
        update_rule = Update_Rule.add_from_pop(self, self.variables._objectify(variable), sym.sympify(equation), description)
        self.update_rules += update_rule

    def _create_window(self, name: str, variables: Variables = None, operators: Operators = None):
        window = Window(name, variables, operators)
        self.windows.append(window)
        setattr(self, name, window)


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
    
    def compile(self):
        self.variables = self.population.variables
        self.parameters = self.population.parameters
        self.update_rules = self.population.update_rules
        self._compute_parameter_graph()
        self._compute_parameters()

    def _compute_parameter_graph(self):
        pass

    def _compute_parameters(self):
        sub_values = zip(self.parameters.get_symbols(), self.parameters.get_contents())
        return sub_values



        









    


    

