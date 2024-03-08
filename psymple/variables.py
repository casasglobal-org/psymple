from functools import reduce
from operator import add
from typing import List  # Deprecated since Python 3.9

import sympy as sym

from psymple.abstract import Container, DependencyError, SymbolWrapper
from psymple.globals import T, sym_custom_ns


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

    def substitute_parameters(self, variables):
        self.update_rule.substitute_parameters(variables)

    def update_buffer(self):
        self.buffer = self.time_series[-1]

    def update_time_series(self, time_step):
        new_value = self.update_rule.evaluate_update(self.buffer, time_step)
        self.time_series.append(new_value)


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
            parameters[self.symbol],
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

    def substitute_parameters(self, variables):
        self.update_rule.substitute_parameters(variables)

    def update_value(self):
        self.computed_value = self.update_rule.evaluate_expression()


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
        variable: Variable,
        equation="0",
        variables: Variables = Variables(),
        parameters: Parameters = Parameters(),
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

        self.variable = variable
        self.equation = sym.sympify(equation, locals=sym_custom_ns)
        self._initialize_dependencies(variables, parameters)
        self.description = description
        self._equation_lambdified = None

    def __str__(self):
        return (
            f"{self.description}: d[{self.variable.symbol}]/dt = {self.equation} "
            f"in variables '{self.variables.get_symbols()}' and parameters "
            f"{self.parameters.get_symbols()}"
        )

    def _initialize_dependencies(
        self, variables: Variables, parameters: Parameters, warn=True
    ):
        """
        Computes variable/parameter dependencies, i.e. the subsets of
        variables/parameters whose symbols appear as free symbols of self.equation.

        Args:
            variables (Variables): Variables that self.equation may contain
            parameters (Parameters): Parameters that equation may contain
            warn (bool): raise an error if there are symbols not accounted for
        """
        variable_symbols = set(variables.get_symbols())
        parameter_symbols = set(parameters.get_symbols())
        all_symbols = variable_symbols | parameter_symbols | {T}
        equation_symbols = sym.sympify(self.equation, locals=sym_custom_ns).free_symbols
        if warn and not equation_symbols.issubset(all_symbols):
            undefined_symbols = equation_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in expression {self.equation}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}"
            )
        equation_variables = [
            variables._objectify(symbol)
            for symbol in equation_symbols.intersection(variable_symbols)
        ]
        equation_parameters = [
            parameters._objectify(symbol)
            for symbol in equation_symbols.intersection(parameter_symbols)
        ]
        self.variables = Variables(equation_variables)
        self.parameters = Parameters(equation_parameters)

    def substitute_parameters(self, variables):
        self.equation = self.equation.subs(
            ((p.symbol, p.expression) for p in self.parameters)
        )
        # All dependent parameters have been subbed out.
        self._initialize_dependencies(variables, Parameters())
        self._equation_lambdified = None

    def _lambdify(self):
        self._equation_lambdified = sym.lambdify(
            self.variables.get_symbols() + self.parameters.get_symbols(),
            self.equation,
            modules=[sym_custom_ns, "scipy", "numpy"],
        )

    def evaluate_expression(self):
        if self._equation_lambdified is None:
            self._lambdify()
        v_args = [v.buffer for v in self.variables]
        p_args = [p.computed_value for p in self.parameters]
        args = v_args + p_args
        return self._equation_lambdified(*args)

    def evaluate_update(self, old_value, time_step):
        value = self.evaluate_expression()
        return old_value + time_step * value

    def get_variables(self):
        return [v.symbol for v in self.variables]

    def get_parameters(self):
        return [p.symbol for p in self.parameters]


class SimUpdateRule(UpdateRule):
    # TODO: substitute_parameters, _lambdify and evaluate_update
    # should be defined within this class, not the more general UpdateRule.
    # However, the UpdateRules._combine always returns an UpdateRule,
    # Rather than the specific class of the input.
    #
    # TODO: Redundancy: SimUpdateRules don't actually need to know their variable
    # because the variable knows the SimUpdateRule.
    # Note: only works for variables, not parameters

    @classmethod
    def from_update_rule(cls, rule, variables, parameters):
        if rule.variable.symbol in variables:
            variable = variables[rule.variable.symbol]
        elif rule.variable.symbol in parameters:
            variable = parameters[rule.variable.symbol]
        else:
            raise ValueError(
                f"Symbol {rule.variable.symbol} neither in "
                f"provided variables {variables} nor parameters {parameters}"
            )
        return SimUpdateRule(
            variable,
            rule.equation,
            variables,
            parameters,
            rule.description,
        )


class UpdateRules(Container):
    def __init__(self, update_rules: list = None):
        super().__init__(update_rules)
        self.update_rules = self.objects
        self.contains_type = UpdateRule
        self.check_duplicates = False

    # def get_combined_update_rules_for_variable(self, variable):
    #     variable_rules = UpdateRules([
    #         update for update in self.update_rules if update.variable == variable
    #     ])
    #     variable.update_rule = new_update_rules._combine(
    #         variable, updates_for_variable
    #     )

    # def get_equations(self):
    #     return [u.equation for u in self]

    # def get_equations_lambdified(self):
    #     return [u._equation_lambdified for u in self]

    def _combine_update_rules(self):
        vars = list(set(u.variable for u in self.objects))
        new_rules = []
        for var in vars:
            updates_for_var = [u for u in self.objects if u.variable == var]
            new_rules.append(self._combine(var, updates_for_var))
        return UpdateRules(new_rules)

    def _combine(self, variable, update_rules):
        try:
            equation = reduce(add, [u.equation for u in update_rules])
        except:
            # Or we need to build in functionality for equation == None (preferred)
            equation = sym.sympify(0)
        variables = Variables(list(set(v for u in update_rules for v in u.variables)))
        parameters = Parameters(
            list(set([p for u in update_rules for p in u.parameters]))
        )
        return UpdateRule(
            variable,
            equation,
            variables,
            parameters,
            f"Combined update rule for variable '{variable.symbol}'",
        )
