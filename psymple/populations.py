import numpy as np

from psymple.abstract import Container
from psymple.variables import (
    Parameter,
    Parameters,
    UpdateRule,
    UpdateRules,
    Variable,
    Variables,
)


class Operator:
    """
    An Operator object will define generic update rules for a Variables object,
    in the same way that an UpdateRule defines
    an update rule for a Variable object.
    """

    def __init__(self, name, function, description):
        self.name = name
        self.operator = function
        self.description = description


class Operators(Container):
    def __init__(self, operators: list = None):
        super().__init__(operators)
        self.operators = self.objects
        self.contains_type = Operator
        self.check_duplicates = False


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


class Population:
    def __init__(self, name: str, initial_value=None):
        self.name = name
        self.variable = Variable.basic(
            name, description=f"{name} population variable", initial_value=initial_value
        )
        self.populations = []
        self.windows = []
        self.variables = Variables([self.variable])
        self.parameters = Parameters()
        self.update_rules = UpdateRules()

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
        update_rule = UpdateRule(
            self.variables._objectify(variable),
            equation,
            self.variables,
            self.parameters,
            description,
        )
        self.update_rules += update_rule

    def _create_window(
        self, name: str, variables: Variables = None, operators: Operators = None
    ):
        window = Window(name, variables, operators)
        self.windows.append(window)
        setattr(self, name, window)


class IndexedPopulation(Population):
    def __init__(self, name: str, shape: tuple):
        super().__init__(name)
        self.array = np.empty(shape, dtype=object)

    def __getitem__(self, index):
        return self.array[index]

    def add_population(self, population, index):
        super()._add_population(population)
        self.array[index] = population
