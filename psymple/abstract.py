from abc import ABC

from sympy import (
    Symbol,
    Basic,
    Number,
    parse_expr,
)

class DependencyError(Exception):
    pass

class ParsingError(Exception):
    pass


class SymbolWrapper(ABC):
    """
    A class storing a `sympy.Symbol` instance with other attributes.
    """
    def __init__(self, symbol: str | Symbol, description: str = ""):
        """
        Create a SymbolWrapper instance.

        Args:
            symbol: the symbol to wrap
            description: an optional description of the container contents
        """
        if isinstance(symbol, str):
            symbol = Symbol(symbol)
        self.symbol = symbol
        self.description = description

    @property
    def name(self):
        return self.symbol.name

    def __repr__(self):
        return f"{type(self).__name__} object: {self.symbol} ({self.description})"
    

class ExpressionWrapper(ABC):
    """
    A class storing a `sympy.Basic` object: anything returned by `sympy.sympify`.
    """
    def __init__(self, expression: Basic | str | float | int, parsing_locals: dict = {}):
        """
        Create an ExpressionWrapper instance

        Args:
            expression: the expression to wrap. If it is not a `sympy` object, it is 
                parsed into one first.
            parsing_locals: a dictionary mapping strings to sympy objects.
        """
        if expression is not None:
            if isinstance(expression, str):
                expression = parse_expr(expression, local_dict=parsing_locals)
            elif isinstance(expression, (int, float)):
                expression = Number(expression)
            if not isinstance(expression, Basic):
                raise ParsingError(f"Expression {expression} of type {type(expression)} is not an accepted type.")
        self.expression = expression
     
class Assignment(ABC):
    """
    Base class for storing a symbol wrapper together with a symbolic expression. An assignment
    is a formal equality between the symbol wrapper and the expression.
    """
    def __init__(self, symbol: str, expression: Basic | str | float | int, parsing_locals: dict={}):
        """
        Instantiate an Assignment.

        Args:
            symbol: LHS of the assignment (e.g. parameter or variable). If input is a string, 
                it is converted to a [SymbolWrapper][psymple.abstract.SymbolWrapper] instance.
            expression: expression on the RHS. If input is a string or number, 
                it is converted to a sympy expression.
            parsing_locals: a dictionary mapping strings to sympy objects.
        """
        self.symbol_wrapper = SymbolWrapper(symbol)
        self.expression_wrapper = ExpressionWrapper(expression, parsing_locals)

    def substitute_symbol(self, old_symbol, new_symbol):
        # Substitutes the symbol inside self.symbol_wrapper with new_symbol
        if self.symbol == old_symbol:
            self.symbol = new_symbol
        self.expression = self.expression.subs(old_symbol, new_symbol)

    def get_free_symbols(self, global_symbols=set([Symbol("T")])):
        # Returns all the symbols of self.expression which are not the symbol wrapper or time symbol
        assignment_symbols = self.expression.free_symbols
        return assignment_symbols - global_symbols - {self.symbol_wrapper.symbol}

    #def to_update_rule(self, variables, parameters):
        """
        Convert to UpdateRules so that it can be used in the Simulation.

        variables/parameters: sympbols that may appear on the RHS of the assignment.
        """
    #    return UpdateRule(self.expression, variables, parameters)
    
    @property
    def symbol(self):
        return self.symbol_wrapper.symbol
    
    @symbol.setter
    def symbol(self, new_symbol):
        self.symbol_wrapper.symbol = new_symbol

    @property
    def expression(self):
        return self.expression_wrapper.expression
    
    @expression.setter
    def expression(self, new_expression):
        self.expression_wrapper.expression = new_expression

    @property
    def name(self):
        return self.symbol_wrapper.name 

    def __repr__(self):
        return f"{type(self).__name__} {self.name} = {self.expression}"
    
    def _to_data(self):
        data = {
            "expression": str(self.expression)
        }
        return data