import unittest

import sympy as sym

from psymple.abstract import Assignment

from psymple.build.assignments import (
    ParameterAssignment,
    DifferentialAssignment,
)

from psymple.build.ported_objects import DependencyError

from psymple.variables import (
    Parameter,
    Variable,
)

class TestCreation(unittest.TestCase):
    def test_symbol_wrapper_parsing(self):
        # Create from string
        assg_1 = Assignment("param", None)

        # Create from symbol
        symbol = sym.Symbol("param")
        assg_2 = Assignment(symbol, None)

        symbol_wrapper_1 = assg_1.symbol_wrapper
        symbol_wrapper_2 = assg_2.symbol_wrapper

        self.assertEqual(symbol_wrapper_1.symbol, symbol_wrapper_2.symbol)

    def test_expression_parsing(self):
        # Create from string
        assg_1 = Assignment("y", "2*x")

        # Create from sympy expression
        expr = 2*sym.Symbol("x")
        assg_2 = Assignment("y", expr)

        self.assertEqual(assg_1.expression, assg_2.expression)

    def test_symbol_wrapper_parameter_coercion(self):
        param_assg = ParameterAssignment("r", "s+t")

        symbol_wrapper = param_assg.symbol_wrapper
        self.assertIsInstance(symbol_wrapper, Parameter)

        self.assertEqual(symbol_wrapper.symbol, sym.Symbol("r"))
        self.assertEqual(symbol_wrapper.value, sym.Symbol("s") + sym.Symbol("t"))

    def test_symbol_wrapper_variable_coercion(self):
        diff_assg = DifferentialAssignment("x", "r*x")

        symbol_wrapper = diff_assg.symbol_wrapper
        self.assertIsInstance(symbol_wrapper, Variable)

        self.assertEqual(symbol_wrapper.symbol, sym.Symbol("x"))

    def test_parameter_assignment_error(self):
        # Parameter assignments cannot have their symbol appearing in expressions
        # but assignment and differential assignment can.

        with self.assertRaises(DependencyError):
            assg_1 = ParameterAssignment("x", "r*x")

        assg_2 = Assignment("x", "r*x")
        assg_3 = DifferentialAssignment("x", "r*x")

class TestHandling(unittest.TestCase):
    def test_symbol_substitution(self):
        x,y,z,r,s,t = sym.symbols("x y z r s t")
        
        assg = Assignment(y, r+s+t)

        assg.substitute_symbol(r, x)
        self.assertEqual(assg.expression, x+s+t)

        assg.substitute_symbol(y, x)
        self.assertEqual(assg.symbol_wrapper.symbol, x)

        assg.substitute_symbol(x, z)
        self.assertEqual(assg.symbol_wrapper.symbol, z)
        self.assertEqual(assg.expression, z+s+t)

    def test_free_symbols(self):
        x, r, s, T = sym.symbols("x r s T")
        assg = Assignment(x, 2*x + r + s + T)

        # By default, T is treated as a global variable
        free_symbols = assg.get_free_symbols()

        self.assertEqual(free_symbols, {r,s})

        free_symbols = assg.get_free_symbols(global_symbols={s, T})

        self.assertEqual(free_symbols, {r})

    def check_combine(self):
        x, r, s = sym.symbols("x r s")
        assg_1 = DifferentialAssignment(x, r*x)
        assg_2 = DifferentialAssignment(x, s*x)

        assg_1.combine(assg_2)

        self.assertEqual(assg_1.expression, (r+s)*x)



