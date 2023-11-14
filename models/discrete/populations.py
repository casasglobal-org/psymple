import sympy as sym
import numpy as np
import networkx as nx
from collections import defaultdict

# from custom_functions import DegreeDays, FFTemperature
from functools import reduce
from operator import add
from typing import List         #Deprecated since Python 3.9

# Create the dictionary passed to sym.sympify and sym.lambdify to convert custom functions
sym_custom_ns = {}
# sym_custom_ns = {'DegreeDays': DegreeDays, 'FFTemperature': FFTemperature}



"""
Symbol_Wrapper classes
"""


class Symbol_Wrapper:
    def __init__(self, symbol: sym.Symbol, description: str):
        self.symbol = symbol
        self.description = description

    def __str__(self):
        return f"{type(self).__name__} object: {self.description} \n {self.symbol}"


class Variable(Symbol_Wrapper):
    def __init__(self, symbol, initial_value, description):
        super().__init__(symbol, description)
        self.initial_value = initial_value

    @classmethod
    def basic(cls, symbol_name, symbol_letter="x", initial_value = None, description=None):
        return cls(
            sym.Symbol(f"{symbol_letter}_{symbol_name}"),
            [initial_value] or [0],
            description or f"{symbol_name} variable",
        )

    @classmethod
    def summary(cls, symbol_name, symbol_letter="s", contents=None, description=None):
        return cls(
            sym.Symbol(f"{symbol_letter}_{symbol_name}"),
            contents,
            description or f"{symbol_name} summary variable",
        )
    
class SimVariable(Variable):
    def __init__(self, variable, time_series = None):
        super().__init__(variable.symbol, variable.initial_value, variable.description)
        self.equation = None
        self.time_series = [self.initial_value]

class Parameter(Symbol_Wrapper):
    def __init__(self, symbol, value, description):
        super().__init__(symbol, description)
        self.value = sym.sympify(value)

    @classmethod
    def basic(cls, symbol_name, symbol_letter, value, description=None):
        return cls(
            sym.Symbol(f"{symbol_letter}_{symbol_name}"),
            value,
            description or f"{symbol_name} basic parameter",
        )

    @classmethod
    def composite(cls, symbol_name, symbol_letter, contents, description=None):
        return cls(
            sym.Symbol(f"{symbol_letter}_{symbol_name}"),
            sym.sympify(contents, locals=sym_custom_ns),
            description or f"{symbol_name} composite parameter",
        )

class SimParameter(Parameter):
    # Possibly not a required class
    def __init__(self, parameter, computed_value = None):
        super().__init__(parameter.symbol, parameter.value, parameter.description)
        self.computed_value = computed_value


"""
Container classes: contain lists of wrapper objects. Contain methods to edit and access these lists.
"""


class Container:
    def __init__(self, objects):
        if objects is None:
            objects = []
        # TODO: check for duplicates in objects on creation
        self.objects = objects
        # self.contains_type = Symbol_Wrapper

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
    
    # TODO: We should define __iter__().

    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(self.objects[index])
        elif isinstance(index, int):
            return self.objects[index]
        elif isinstance(index, (str, sym.Symbol)):
            return self._objectify(index)

    def _duplicates(self, list, object):
        if object in list:
            raise Exception(
                f"The symbol '{object}' has already been defined. Try a new symbol."
            )

    def _edit(self, edit_type, index=None, object=None):
        if edit_type == "remove":
            del self.objects[index]
        elif edit_type == "replace":
            self._duplicates(self.objects, object)
            self[index] = object
        elif edit_type == "add":
            self._duplicates(self.objects, object)
            self.objects += [object]

    def _objectify(self, expr):
        if isinstance(expr, str) or isinstance(expr, sym.Symbol):
            return next(obj for obj in self if obj.symbol == sym.sympify(expr, locals=sym_custom_ns))
        elif isinstance(expr, self.contains_type):
            return expr
        else:
            raise TypeError(
                f"arguments to _objectify should be of type {repr(str)}, {repr(sym.Symbol)} or {self.contains_type}"
            )


class Variables(Container):
    def __init__(self, variables: List[Variable] = None):
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
    def __init__(self, parameters: List[Parameter] = None):
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
        vars = list(set(u.variable for u in self))
        new_rules = []
        for var in vars:
            updates_for_var = [u for u in self if u.variable == var]
            new_rules.append(self._combine(var, updates_for_var))
        return Update_Rules(new_rules)

    def _combine(self, variable, update_rules):
        equations = reduce(add, [u.equation for u in update_rules])
        variables = Variables(
            list(set([v for u in update_rules for v in u.variables]))
        )
        parameters = Parameters(
            list(set([p for u in update_rules for p in u.parameters]))
        )
        return Update_Rule(
            variable,
            equations,
            variables,
            parameters,
            f"Combined update rule for variable '{variable.symbol}'",
        )


class Operators(Container):
    def __init__(self, operators: list = None):
        super().__init__(operators)
        self.operators = self.objects
        self.contains_type = Operator
        self.check_duplicates = False


"""
Equation wrapper clases
TODO: abstract Equation_Wrapper class? Need to see how Operator class develops
"""


class Update_Rule:
    # TODO: need to go through (at refactor) what checks we want to do eagerly (eg. equation completeness), and which
    #       we want to happen at compile. If none, then update_rule doesn't need to store its variable and 
    #       parameter dependencies.
    def __init__(
        self,
        variable: Variable,
        equation,
        variables: Variables,
        parameters: Parameters,
        description: str,
    ):
        self.variable = variable
        self.equation = sym.sympify(equation, locals=sym_custom_ns)
        self.variables = variables
        self.parameters = parameters
        self.description = description
        self.equation_lambdified = None
        #self._check_equation_completeness()

    @classmethod
    def add_from_pop(cls, pop, variable: Variable, equation, description=None):
        equation_variables, equation_parameters = cls._get_dependencies(equation, pop.variables, pop.parameters, warn = True)
        return cls(
            variable,
            equation,
            equation_variables,
            equation_parameters,
            description or f"{variable.symbol} update rule",
        )

    def __str__(self):
        return f"{self.description}: d[{self.variable.symbol}]/dt = {self.equation} in variables '{self.variables.get_symbols()}' and parameters {self.parameters.get_symbols()}"

    @staticmethod
    def _get_dependencies(equation, variables: Variables, parameters: Parameters, warn = True):
        '''
        Returns the sublists of variables and parameters whose symbols appear as free symbols of self.equation

        Args:
            variables (Variables)
            parameters (Parameters)
            warn (bool): raise an error if there are symbols not accounted for
        '''
        variable_symbols = set(variables.get_symbols())
        parameter_symbols = set(parameters.get_symbols())
        equation_symbols = sym.sympify(equation, locals=sym_custom_ns).free_symbols
        if warn and not equation_symbols.issubset(variable_symbols.union(parameter_symbols)):
            print("Unaccounted symbols in equation")
        equation_variables = [variables._objectify(symbol) for symbol in equation_symbols.intersection(variable_symbols)]
        equation_parameters = [parameters._objectify(symbol) for symbol in equation_symbols.intersection(parameter_symbols)]
        return Variables(equation_variables), Parameters(equation_parameters)

    def _check_equation_completeness(self):
        variable_symbols = self.variables.get_symbols()
        parameter_symbols = self.parameters.get_symbols()
        equation_symbols = self.equation.free_symbols
        difference = equation_symbols - set(variable_symbols + parameter_symbols)
        if difference:
            raise Exception(
                f"The {'symbol' if len(difference) == 1 else 'symbols'} '{difference}' in equation '{self.equation}' {'does' if len(difference) == 1 else 'do'} not have an associated {Variable.__name__} object."
            )

    def get_variables(self):
        return [v.symbol for v in self.variables]

    def get_parameters(self):
        return [p.symbol for p in self.parameters]


class Operator:
    """
    An Operator object will define generic update rules for a Variables object, in the same way that an Update_Rule defines
    an update rule for a Variable object.
    """

    def __init__(self, name, function, description):
        self.name = name
        self.operator = function
        self.description = description


"""
Population classes
"""

T = sym.Symbol("T")
time = SimVariable(Variable(T, 0, "system time"))


class Population:
    def __init__(self, name: str):
        self.name = name
        self.variable = Variable.basic(name, description=f"{name} population variable")
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

    def _add_parameter(
        self, type, symbol_name, symbol_letter, contents, description=None
    ):
        if type == "basic":
            param = Parameter.basic(symbol_name, symbol_letter, contents, description)
        elif type == "composite":
            param = Parameter.composite(
                symbol_name, symbol_letter, contents, description
            )
        self.parameters += param
        setattr(self.parameters, symbol_name, param)

    def _add_update_rule(self, variable, equation, description=None):
        update_rule = Update_Rule.add_from_pop(
            self, self.variables._objectify(variable), equation, description
        )
        self.update_rules += update_rule

    def _create_window(
        self, name: str, variables: Variables = None, operators: Operators = None
    ):
        window = Window(name, variables, operators)
        self.windows.append(window)
        setattr(self, name, window)

    def compile(self):
        return System(self)


class Indexed_Population(Population):
    def __init__(self, name: str, shape: tuple):
        super().__init__(name)
        self.array = np.empty(shape, dtype=object)

    def __getitem__(self, index):
        return self.array[index]

    def add_population(self, population, index):
        super()._add_population(population)
        self.array[index] = population


"""
Window classes
"""


class Window:
    def __init__(
        self,
        name: str,
        variables: Variables = Variables(),
        operators: Operators = Operators(),
    ):
        self.name = name
        self.variables = variables
        self.operators = operators

    def _add_operator(self, name, function, description=None):
        operator = Operator(
            name, function, description or f"{self.name} operator: {name}"
        )
        self.operators += operator
        setattr(self, name, operator)


"""
System
"""


class PopulationSystemError(Exception):
    pass





class System():
    def __init__(self, population):
        self.population = population
        self.variables = Variables([time])
        self.parameters = Parameters()
        self.update_rules = self.population.update_rules._combine_update_rules()
        # If the calls below happen during construction, we need to think about
        # how to write tests for each of these components.
        # self._compute_parameter_update_order()  
        self._create_variables(population.variables)
        self._create_parameters(population.parameters)
        self._compute_parameters()
        #self._lambify_update_rules()

    # TODO: How to update the Variable in each update rule to the corresponding SimVariable?

    def _create_variables(self, variables):
        self.variables += Variables([SimVariable(variable) for variable in variables])

    def _create_parameters(self, parameters):
        self.parameters += Parameters([SimParameter(parameter) for parameter in parameters])

    def _compute_parameter_update_order(self):
        variable_symbols = {v.symbol for v in self.variables}
        parameter_symbols = {p.symbol: p for p in self.parameters}
        G = nx.DiGraph()
        G.add_nodes_from(parameter_symbols)
        for parameter in self.parameters:
            parsym = parameter.symbol
            dependencies = parameter.value.free_symbols
            for dependency in dependencies:
                if dependency in parameter_symbols:
                    G.add_edge(dependency, parsym)
                elif dependency not in variable_symbols:
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

    def _compute_parameters(self):
        ordered_parameters = self._compute_parameter_update_order()
        sub_list = []
        for parameter in ordered_parameters:
            parameter.computed_value = parameter.value.subs(sub_list)
            sub_list.append((parameter.symbol, parameter.computed_value))
        

    def _lambify_update_rules(self):
        for u in self.update_rules:
            u.equation_lambdified = sym.lambdify(
                [u.variables.get_symbols() + self.system_variables.get_symbols()],
                u.equation,
            )

    def _wrap_for_solve_ivp(self, *args):
        """
        returns a callable function of all system variables for use with solve_ivp, wrapping lambdified update rules
        """
        # FIXME: doesn't work with the solve_ivp function call signature of f(t,[y0,y1,...]) yet. Needs a deeper think about how time
        # is handled generally.
        return [
            u.equation_lambdified(
                [
                    args[i]
                    for i in [self.variables.objects.index(v) for v in u.variables]
                ]
            )
            for u in self.update_rules
        ]

    def advance_time(self, time_step):
        for v in self.variables:
            v.buffer = v.time_series[-1]
        for u in self.update_rules:
            u.variable.time_series.append(
                u.variable.buffer
                + time_step
                * u.equation_lambdified(
                    [v.buffer for v in u.variables]
                    + [v.buffer for v in self.system_variables]
                )
            )
        self.system_time.time_series.append(
            self.system_time.time_series[-1] + time_step
        )

    def advance_time_unit(self, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                f"Number of time steps in a day must be a positive integer, not '{n_steps}'."
            )
        for i in range(n_steps):
            self.advance_time(1 / n_steps)

    def simulate(self, t_end, n_steps):
        if n_steps <= 0 or not isinstance(n_steps, int):
            raise ValueError(
                f"Simulation time must terminate at a positive integer, not '{n_steps}'."
            )
        for i in range(t_end):
            self.advance_time_unit(n_steps)
