from functools import reduce
from operator import add
from typing import List  # Deprecated since Python 3.9

import sympy as sym

from psymple.abstract import DependencyError, SymbolWrapper
from psymple.globals import T, sym_custom_ns

class Container(dict):
    def __getitem__(self, item):
        if isinstance(item, str):
           item = sym.Symbol(item)
        return super().__getitem__(item)       

class Variable(SymbolWrapper):
    def __init__(self, symbol, initial_value, description=""):
        super().__init__(symbol, description)
        self.initial_value = initial_value

    @classmethod
    def basic(
        cls, symbol_name, symbol_letter="x", initial_value=None, description=None
    ):
        return cls(
            sym.Symbol(f"{symbol_letter}_{symbol_name}"),
            initial_value,
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
    def __init__(self, variable, time_series=None):
        super().__init__(variable.symbol, variable.initial_value, variable.description)
        self.update_rule = None
        self.time_series = [self.initial_value]
        self.buffer = self.initial_value

    def set_update_rule(self, update_rule):
        self.update_rule = update_rule


class Parameter(SymbolWrapper):
    def __init__(self, symbol, value, description=""):
        super().__init__(symbol, description)
        self.value = sym.sympify(value, locals=sym_custom_ns)

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
    def __init__(self, parameter, computed_value=None):
        super().__init__(parameter.symbol, parameter.value, parameter.description)
        # TODO: Redundancy:
        # The value attribute inherited from Parameter is redundant here
        # because it's implicit in the UpdateRule.
        self.computed_value = computed_value
        self.update_rule = None

    def initialize_update_rule(self, variables, parameters):
        self.update_rule = SimUpdateRule(
            #parameters[self.symbol],
            self.value,
            variables,
            parameters,
            f"UpdateRule for {self.symbol} ({self.description})",
        )

    def dependent_parameters(self):
        return self.update_rule.parameters

    def set_update_rule(self, update_rule):
        self.update_rule = update_rule

    @property
    def expression(self):
        return self.update_rule.equation


class UpdateRule:
    """
    Equation wrapper clases

    TODO: abstract Equation_Wrapper class? Need to see how Operator class develops
    TODO: need to go through (at refactor) what checks we want to do eagerly
        (eg. equation completeness), and which we want to happen at compile.
        If none, then update_rule doesn't need to store its variable and
        parameter dependencies, and we create a 'SimUpdateRule' class to attach
        to SimVariables in System.
    """

    def __init__(
        self,
        equation="0",
        variables: set = {},
        parameters: set = {},
        description: str = "",
    ):
        """
        An update rule is a expression/equation that is used for updating
        a referenced variable (or parameter). At any given point in time,
        the update rule knows what variables and parameters its expression
        depends on, and does not contain any other symbols (with the exception
        of T, the time symbol, and global function names.)
        TODO: Proper handling of global functions.

        Args:
            variable: the variable/parameter the UpdateRule is for,
            equation: the expression
            variables: dependent variables
            parameters: dependent parameters
            description: short description of the rule
        """

        self.equation = sym.sympify(equation, locals=sym_custom_ns)
        self._initialize_dependencies(variables, parameters)
        self.description = description
        self._equation_lambdified = None

    def _initialize_dependencies(
        self, variables: set, parameters: set, warn=True
    ):
        """
        Computes variable/parameter dependencies, i.e. the subsets of
        variables/parameters whose symbols appear as free symbols of self.equation.

        Args:
            variables (Variables): Variables that self.equation may contain
            parameters (Parameters): Parameters that equation may contain
            warn (bool): raise an error if there are symbols not accounted for
        """
        all_symbols = variables | parameters
        equation_symbols = sym.sympify(self.equation, locals=sym_custom_ns).free_symbols
        if warn and not equation_symbols.issubset(all_symbols):
            undefined_symbols = equation_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in expression {self.equation}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}"
            )
        equation_variables = equation_symbols.intersection(variables)
        equation_parameters = equation_symbols.intersection(parameters)
        self.variables = equation_variables
        self.parameters = equation_parameters

    def _lambdify(self):
        self._equation_lambdified = sym.lambdify(
            tuple(self.variables | self.parameters),
            self.equation,
            modules=[sym_custom_ns, "scipy", "numpy"],
            cse=True,
        )

    def get_variables(self):
        return [v.symbol for v in self.variables]

    def get_parameters(self):
        return [p.symbol for p in self.parameters]


class SimUpdateRule(UpdateRule):
    # TODO: substitute_parameters, _lambdify and evaluate_update
    # should be defined within this class, not the more general UpdateRule.
    # However, the UpdateRules._combine always returns an UpdateRule,
    # Rather than the specific class of the input.

    @classmethod
    def from_update_rule(cls, rule, variables, parameters):
        return SimUpdateRule(
            rule.equation,
            variables,
            parameters,
            rule.description,
        )