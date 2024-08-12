import unittest

import sympy as sym

from psymple.ported_objects import (
    Assignment,
    FunctionalPortedObject,
    FunctionalAssignment,
    VariablePortedObject,
    DifferentialAssignment,
    DefaultParameterAssignment,
    Port,
    InputPort,
    OutputPort,
    VariablePort,
    CompiledPort,
    CompiledInputPort,
    CompiledOutputPort,
    CompiledVariablePort,
    DependencyError,
)

from psymple.variables import (
    Parameter,
)

class TestPorts(unittest.TestCase):
    def test_port_creation(self):
        P_1 = Port("P_1")

        # Port name cannot contain "."
        with self.assertRaises(ValueError):
            P_2 = Port("P.2")

        # Test symbol creation
        symbol = sym.Symbol("P_1")

        self.assertEqual(P_1.symbol, symbol)

    def test_compiled_ports(self):
        P = Port("P")
        assg = Assignment("y", "2*x")

        P_c = CompiledPort(P, assg)

        self.assertEqual(P_c.name, "P")
        # New assignment should be a copy
        self.assertNotEqual(P_c.assignment, assg)

        self.assertEqual(P_c.assignment.symbol, sym.Symbol("y"))
        self.assertEqual(P_c.assignment.expression, 2*sym.Symbol("x"))

    def test_compiled_symbol_substitution_no_assignment(self):
        P = Port("P")

        P_c = CompiledPort(P, None)

        P, Q, R = sym.symbols("P Q R")

        P_c.substitute_symbol(Q, R)
        self.assertEqual(P_c.symbol, P)

        P_c.substitute_symbol(P, Q)
        self.assertEqual(P_c.symbol, Q)

    def test_compiled_symbol_substitition_with_assignment(self):
        P = Port("P")

        x, y, z = sym.symbols("x y z")
        assg = Assignment(y, 2*x)

        P_c = CompiledPort(P, assg)
        self.assertEqual(P_c.symbol, sym.Symbol("P"))
        
        P_c.substitute_symbol(y, z)
        # Port symbol should now align with assignment symbol
        self.assertEqual(P_c.symbol, z)
        self.assertEqual(P_c.assignment.symbol, z)
        self.assertEqual(P_c.assignment.expression, 2*x)

        P_c.substitute_symbol(x, y)
        self.assertEqual(P_c.symbol, z)
        self.assertEqual(P_c.assignment.symbol, z)
        self.assertEqual(P_c.assignment.expression, 2*y)

class TestCompile(unittest.TestCase):
    # Test compilation features, prefixing
    pass

class TestFunctionalPortedObjects(unittest.TestCase):
    def test_single_port_creation(self):
        with self.assertRaises(ValueError):
            fpo = FunctionalPortedObject(
                name="test_func",
                assignments=[("y", "2*x")],
                create_input_ports=False,
            )

        fpo = FunctionalPortedObject(
            name="test_func",
            assignments=[("y", "2*x")],
            create_input_ports=True,
        )

        self.assertEqual(len(fpo.input_ports), 1)
        self.assertIn("x", fpo.input_ports)
        self.assertEqual(len(fpo.output_ports), 1)
        self.assertIn("y", fpo.output_ports)

    def test_mutiple_port_creation(self):
        with self.assertRaises(ValueError):
            fpo = FunctionalPortedObject(
                name="test_func",
                input_ports = ["r"],
                assignments=[("y", "r + s + t")],
                create_input_ports=False,
            )
        
        fpo = FunctionalPortedObject(
            name="test_func",
            input_ports = ["r"],
            assignments=[("y", "r + s + t")],
            create_input_ports=True,
        )

        self.assertEqual(len(fpo.input_ports), 3)
        self.assertIn("r", fpo.input_ports.keys())
        self.assertIn("s", fpo.input_ports.keys())
        self.assertIn("t", fpo.input_ports.keys())

        self.assertIn("y", fpo.output_ports)

    def test_input_port_default_value(self):
        fpo = FunctionalPortedObject(
            name="func_test",
            input_ports=[("x", 10)],
            assignments=[("y", "2*x")],
        )

        self.assertIn("x", fpo.input_ports)
        self.assertEqual(fpo.input_ports["x"].default_value, 10)

    def test_functional_assignment_creation(self):
        fpo = FunctionalPortedObject(
            name="func_test",
            input_ports=[("x", 10)],
            assignments=[("y", "2*x")],
        )

        self.assertIn("y", fpo.assignments)
        
        assg = fpo.assignments["y"]
        self.assertIsInstance(assg, FunctionalAssignment)

        symbol = assg.symbol_wrapper
        expr = assg.expression

        self.assertIsInstance(symbol, Parameter)
        self.assertEqual(symbol.symbol, sym.Symbol("y"))
        self.assertEqual(symbol.value, 2*sym.Symbol("x"))

        self.assertEqual(expr, 2*sym.Symbol("x"))    

        compiled = fpo.compile()

        self.assertIn("x", compiled.input_ports)
        self.assertEqual(compiled.input_ports["x"].default_value, 10)

        self.assertIn("y", compiled.output_ports)
        assg_compiled = compiled.output_ports["y"].assignment
        
        # Compiled assignment should be a deep copy of the original assignment
        self.assertNotEqual(assg_compiled, assg)

        # Check the copied assignment has the same features
        symbol = assg_compiled.symbol_wrapper
        expr = assg_compiled.expression

        self.assertIsInstance(symbol, Parameter)
        self.assertEqual(symbol.symbol, sym.Symbol("y"))
        self.assertEqual(symbol.value, 2*sym.Symbol("x"))

        self.assertEqual(expr, 2*sym.Symbol("x"))

    def test_default_assignment_creation(self):
        fpo = FunctionalPortedObject(
            name="func_test",
            input_ports=[("x", 10)],
            assignments=[("y", "2*x")],
        )

        compiled=fpo.compile()

        self.assertIn("x", compiled.input_ports)

        compiled.set_input_parameters()

        # This should replace the input port with a default parameter assignment
        self.assertNotIn("x", compiled.input_ports)
        
        self.assertIn("x", compiled.internal_parameter_assignments)
        assg = compiled.internal_parameter_assignments["x"]

        self.assertIsInstance(assg, DefaultParameterAssignment)
        self.assertEqual(assg.expression, 10)

    def test_fpo_prefixing(self):
        fpo = FunctionalPortedObject(
            name="func_test",
            assignments=[("y", "2*x")],
        )

        # Test prefixing of symbols with PO name
        compiled = fpo.compile(prefix_names=True)
        in_port = compiled.input_ports["x"]
        out_port = compiled.output_ports["y"]
        self.assertEqual(in_port.name, "func_test.x")
        self.assertEqual(out_port.name, "func_test.y")
        self.assertEqual(out_port.assignment.expression, 2 * sym.Symbol("func_test.x"))

        # No prefixing
        compiled = fpo.compile()
        in_port = compiled.input_ports["x"]
        out_port = compiled.output_ports["y"]
        self.assertEqual(in_port.name, "x")
        self.assertEqual(out_port.name, "y")
        self.assertEqual(out_port.assignment.expression, 2 * sym.Symbol("x"))


class TestVariablePortedObjects(unittest.TestCase):
    def test_variable_port_creation(self):
        vpo_1 = VariablePortedObject(
            name="vpo_test",
            assignments=[
                ("x_1", "2*x_1+x_2"),
                ("x_2", "x_2 - x_1/2"),
            ]
        )
        self.assertEqual(len(vpo_1.variable_ports), 2)
        self.assertIn("x_1", vpo_1.variable_ports)
        self.assertIn("x_2", vpo_1.variable_ports)

        vpo_2 = VariablePortedObject(
            name="var_test",
            variable_ports=["x_1"],
            assignments=[
                ("x_1", "2*x_1+x_2"),
                ("x_2", "x_2 - x_1/2"),
            ]
        )
        self.assertEqual(len(vpo_2.variable_ports), 1)
        self.assertIn("x_1", vpo_2.variable_ports)
        self.assertIn("x_2", vpo_2.internals)

    def test_input_port_creation(self):
        vpo_1 = VariablePortedObject(
            name="vpo_test",
            assignments=[
                ("x_1", "r_1*x_1 - x_2"),
                ("x_2", "r_2*x_2"),
            ]
        )
        self.assertEqual(len(vpo_1.input_ports), 2)
        self.assertIn("r_1", vpo_1.input_ports)
        self.assertIn("r_2", vpo_1.input_ports)

        vpo_2 = VariablePortedObject(
            name="vpo_test",
            input_ports=["r_1"],
            assignments=[
                ("x_1", "r_1*x_1 - x_2"),
                ("x_2", "r_2*x_2"),
            ]
        )
        self.assertEqual(len(vpo_2.input_ports), 2)
        self.assertIn("r_1", vpo_2.input_ports)
        self.assertIn("r_2", vpo_2.input_ports)

        # Test not creating r_2 port manually or automatically. No errors
        # should be thrown until compile, unless the port is added.
        vpo_3 = VariablePortedObject(
            name="vpo_test",
            input_ports=["r_1"],
            assignments=[
                ("x_1", "r_1*x_1 - x_2"),
                ("x_2", "r_2*x_2"),
            ],
            create_input_ports=False
        )
        self.assertEqual(len(vpo_3.input_ports), 1)
        self.assertIn("r_1", vpo_3.input_ports)
        self.assertNotIn("r_2", vpo_3.input_ports)













        






