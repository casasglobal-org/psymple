from functools import reduce
from operator import add
from typing import List  # Deprecated since Python 3.9

import sympy as sym
from models.abstract import Container, SymbolWrapper
from models.globals import sym_custom_ns


class Variable(SymbolWrapper):
    def __init__(self, symbol, initial_value, description):
        super().__init__(symbol, description)
        self.initial_value = initial_value

    @classmethod
    def basic(
        cls, symbol_name, symbol_letter="x", initial_value=None, description=None
    ):
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
    def __init__(self, variable, time_series=None):
        super().__init__(variable.symbol, variable.initial_value, variable.description)
        self.update_rule = None
        self.time_series = [self.initial_value]
        self.buffer = self.initial_value

    def sub_parameters(self):
        self.update_rule.sub_parameters()

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
    def __init__(self, parameter, computed_value=None):
        super().__init__(parameter.symbol, parameter.value, parameter.description)
        self.computed_value = computed_value


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
        self._equation_lambdified = None
        # self._check_equation_completeness()

    @classmethod
    def add_from_pop(cls, pop, variable: Variable, equation, description=None):
        equation_variables, equation_parameters = cls._get_dependencies(
            equation, pop.variables, pop.parameters, warn=True
        )
        return cls(
            variable,
            equation,
            equation_variables,
            equation_parameters,
            description or f"{variable.symbol} update rule",
        )

    def __str__(self):
        return (
            f"{self.description}: d[{self.variable.symbol}]/dt = {self.equation} "
            f"in variables '{self.variables.get_symbols()}' and parameters "
            f"{self.parameters.get_symbols()}"
        )

    @staticmethod
    def _get_dependencies(
        equation, variables: Variables, parameters: Parameters, warn=True
    ):
        """
        Returns the sublists of variables and parameters whose symbols appear as
        free symbols of self.equation

        Args:
            variables (Variables)
            parameters (Parameters)
            warn (bool): raise an error if there are symbols not accounted for
        """
        variable_symbols = set(variables.get_symbols())
        parameter_symbols = set(parameters.get_symbols())
        equation_symbols = sym.sympify(equation, locals=sym_custom_ns).free_symbols
        if warn and not equation_symbols.issubset(
            variable_symbols.union(parameter_symbols)
        ):
            print("Unaccounted symbols in equation")
        equation_variables = [
            variables._objectify(symbol)
            for symbol in equation_symbols.intersection(variable_symbols)
        ]
        equation_parameters = [
            parameters._objectify(symbol)
            for symbol in equation_symbols.intersection(parameter_symbols)
        ]
        return Variables(equation_variables), Parameters(equation_parameters)

    def _check_equation_completeness(self):
        variable_symbols = self.variables.get_symbols()
        parameter_symbols = self.parameters.get_symbols()
        equation_symbols = self.equation.free_symbols
        difference = equation_symbols - set(variable_symbols + parameter_symbols)
        if difference:
            raise Exception(
                f"The {'symbol' if len(difference) == 1 else 'symbols'} "
                f"'{difference}' in equation '{self.equation}' "
                f"{'does' if len(difference) == 1 else 'do'} not have an "
                f"associated {Variable.__name__} object."
            )

    def sub_parameters(self):
        # TODO: We now need to update the variable dependencies
        # with the parameter dependencies that we introduced.
        # Without this, parameters cannot contain references to variables (including T)
        self.equation = self.equation.subs(
            ((p.symbol, p.computed_value) for p in self.parameters)
        )
        # All dependent parameters have been subbed out.
        self.parameters = Parameters()
        self._equation_lambdified = None

    def _lambdify(self):
        self._equation_lambdified = sym.lambdify(
            self.variables.get_symbols() + self.parameters.get_symbols(),
            self.equation,
        )

    def evaluate_update(self, old_value, time_step):
        if self._equation_lambdified is None:
            self._lambdify()
        v_args = [v.buffer for v in self.variables]
        p_args = [p.computed_value for p in self.parameters]
        args = v_args + p_args
        return old_value + time_step * self._equation_lambdified(*args)

    def get_variables(self):
        return [v.symbol for v in self.variables]

    def get_parameters(self):
        return [p.symbol for p in self.parameters]


class SimUpdateRule(UpdateRule):
    def __init__(self, update_rule):
        super().__init__(
            update_rule.variable,
            update_rule.equation,
            update_rule.variables,
            update_rule.parameters,
            update_rule.description,
        )


class UpdateRules(Container):
    def __init__(self, update_rules: list = None):
        super().__init__(update_rules)
        self.update_rules = self.objects
        self.contains_type = UpdateRule
        self.check_duplicates = False

    # def get_equations(self):
    #     return [u.equation for u in self]

    # def get_equations_lambdified(self):
    #     return [u._equation_lambdified for u in self]

    def _combine_update_rules(self):
        vars = list(set(u.variable for u in self))
        new_rules = []
        for var in vars:
            updates_for_var = [u for u in self if u.variable == var]
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
