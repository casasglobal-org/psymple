from sympy import Expr

from psymple.abstract import (
    Assignment,
    SymbolWrapper,
    DependencyError,
)

from psymple.variables import Variable, Parameter


class DifferentialAssignment(Assignment):
    """
    Class storing an ODE of the form \( dx/dt = f(x,t,b) \) where \( b \) is a list of 
    external dependencies.

    Methods:
        combine
    """
    def __init__(self, symbol: str, expression: Expr | str | float | int, parsing_locals: dict={}):
        """
        Intantiate a DifferentialAssignment. 

        Args:
            symbol: LHS of the assignment containing the variable derivative. 
                If input is a string, it is converted to a [SymbolWrapper][psymple.abstract.SymbolWrapper] instance.
            expression: function on the RHS. If input is a string or number, 
                it is converted to a sympy expression.
            parsing_locals: a dictionary mapping strings to sympy objects.
        """
        super().__init__(symbol, expression, parsing_locals)
        # Coerce self.symbol_wrapper into instance of Variable.
        if type(self.symbol_wrapper) is SymbolWrapper:
            self.symbol_wrapper = Variable(
                symbol=self.symbol_wrapper.symbol,
                description=self.symbol_wrapper.description,
            )

    @property
    def variable(self):
        return self.symbol_wrapper

    def __repr__(self):
        return f"DifferentialAssignment d({self.name})/dt = {self.expression}"

    def combine(self, other):
        # Combine the expressions of two DifferentialAssignment instances.
        self.expression += other.expression

    def _to_data(self):
        data = super()._to_data()
        data.update(
            {
                "variable": self.name
            }
        )
        return data


class ParameterAssignment(Assignment):
    """
    Class storing an assignment of the form \( y = f(x,t,b) \), where \( b \) is a list of
    external dependencies.
    """
    def __init__(self, symbol: str, expression: Expr | str | float | int, parsing_locals: dict={}):
        """
        Instantiate a ParameterAssignment. 

        Args:
            symbol: LHS of the assignment containing the parameter name. 
                If input is a string, it is converted to a [SymbolWrapper][psymple.abstract.SymbolWrapper] instance.
            expression: function on the RHS. If input is a string or number, 
                it is converted to a sympy expression.
            parsing_locals: a dictionary mapping strings to sympy objects.
        """
        super().__init__(symbol, expression, parsing_locals)
        # We ensure we that the symbol_wrapper is instance of Parameter.
        if type(self.symbol_wrapper) is SymbolWrapper:
            self.symbol_wrapper = Parameter(
                self.symbol_wrapper.symbol,
                self.expression,
                self.symbol_wrapper.description,
            )
        # We forbid the symbol wrapper to appear in the expression eg. R=2*R
        if self.symbol in self.expression.free_symbols:
            raise DependencyError(
                f"The symbol {self.symbol} cannot appear as both the function "
                f"value and argument of {self}."
            )

    # Parameters have this annoying data redundancy in that they also
    # store their own value. This is already in expression.
    # So we need to copy that over.
    def _sync_param_value(self):
        self.parameter.value = self.expression

    def substitute_symbol(self, old_symbol, new_symbol):
        super().substitute_symbol(old_symbol, new_symbol)
        self._sync_param_value()

    @property
    def parameter(self):
        return self.symbol_wrapper
    
    def _to_data(self):
        data = super()._to_data()
        data.update(
            {
                "parameter": self.name
            }
        )
        return data


class DefaultParameterAssignment(ParameterAssignment):
    """
    A convenience class to identify parameters which have been constructed from default values.
    These represent those system parameters which are changeable.
    """

class FunctionalAssignment(ParameterAssignment):
    """
    A convenience class to identify parameters which have been constructed from the OutputPort
    of a FunctionalPortedObject. These represent the core functional building blocks of a
    System.
    """