import unittest

import sympy as sym

from psymple.abstract import Assignment

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
)

from psymple.build.assignments import (
    DefaultParameterAssignment,
    FunctionalAssignment,
)

from psymple.build.compiled_ports import CompiledPort

from psymple.build.ports import Port

from psymple.build.ported_objects import (
    WiringError,
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
    def test_fpo_compile(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            input_ports=[("s", 1), ("t", 2)],
            assignments=[("r", "s+t")],
        )

        compiled = fpo.compile()

        self.assertEqual(compiled.input_ports.keys(), {"s", "t"})
        port_s = compiled.input_ports["s"]
        port_t = compiled.input_ports["t"]

        self.assertEqual(compiled.output_ports.keys(), {"r"})
        port_r = compiled.output_ports["r"]

        s, t = sym.symbols("s, t")
        self.assertEqual(port_r.assignment.expression, s+t)

        self.assertEqual(port_s.default_value, 1)
        self.assertEqual(port_t.default_value, 2)

    def test_vpo_compile(self):
        vpo = VariablePortedObject(
            name="vpo",
            input_ports=[("r", 1)],
            variable_ports=["x"],
            assignments=[("x", "r*y"), ("y", "x")],
        )

        compiled = vpo.compile()

        self.assertEqual(compiled.input_ports.keys(), {"r"})
        port_r = compiled.input_ports["r"]
        self.assertEqual(compiled.variable_ports.keys(), {"x"})
        port_x = compiled.variable_ports["x"]
        self.assertEqual(compiled.internal_variable_assignments.keys(), {"y"})
        assg_y = compiled.internal_variable_assignments["y"]

        r, x, y = sym.symbols("r, x, y")
        self.assertEqual(port_r.default_value, 1)
        self.assertEqual(port_x.assignment.expression, r*y)
        self.assertEqual(assg_y.expression, x)

    def test_prefix_names(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            input_ports=[("s", 1)],
            assignments=[("r", "2*s")],
        )

        compiled = fpo.compile(prefix_names=False)

        self.assertEqual(compiled.input_ports.keys(), {"s"})
        self.assertEqual(compiled.output_ports.keys(), {"r"})

        assg = compiled.output_ports["r"].assignment
        self.assertEqual(assg.name, "r")
        self.assertEqual(assg.expression, 2*sym.Symbol("s"))

        # When names are prefixed, only the assignment symbols are substituted, not the dictionary keys
        compiled = fpo.compile(prefix_names=True)

        self.assertEqual(compiled.input_ports.keys(), {"s"})
        self.assertEqual(compiled.output_ports.keys(), {"r"})

        assg = compiled.output_ports["r"].assignment
        self.assertEqual(assg.name, "fpo.r")
        self.assertEqual(assg.expression, 2*sym.Symbol("fpo.s"))
    
    def test_cpo_compile_directed_wires(self):
        fpos = [
            FunctionalPortedObject(
                name=f"fpo_{i}",
                input_ports=[("s", 2)],
                assignments=[("r", f"{i+1}*s")],
            )
            for i in range(3)
        ]

        # Test 1 - an input port cannot be connected to by more than one directed wire 
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", "fpo_0.s"), 
                ("b", "fpo_0.s"),
            ]
        )
        
        with self.assertRaises(WiringError):
            cpo.compile()

        # Test 2 - a directed wire cannot go to two output ports
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("fpo_0.r", ["r", "s"]), 
            ]
        )
        
        with self.assertRaises(WiringError):
            cpo.compile()

        # Test 3 - A wire cannot go straight from an input port to an output port of cpo
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", "r"), 
            ]
        )
        
        with self.assertRaises(WiringError):
            cpo.compile()

        # Test 4 - A wire cannot include a branch from an input port to an output port of cpo
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", ["r", "fpo_0.s"]), 
            ]
        )
        
        with self.assertRaises(WiringError):
            cpo.compile()

        # Test 5 - A wire can connect an input port to multiple child input ports
        # whose symbols are overwritten.
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", ["fpo_0.s", "fpo_1.s"]), 
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"fpo_0.r", "fpo_1.r", "fpo_2.r", "fpo_2.s"})

        assg_0 = compiled.internal_parameter_assignments["fpo_0.r"]
        assg_1 = compiled.internal_parameter_assignments["fpo_1.r"]
        assg_2 = compiled.internal_parameter_assignments["fpo_2.r"]
        assg_2_in = compiled.internal_parameter_assignments["fpo_2.s"]

        a, fpo_2_s = sym.symbols("a, fpo_2.s")
        self.assertEqual(assg_0.expression, a)
        self.assertEqual(assg_1.expression, 2*a)
        self.assertEqual(assg_2.expression, 3*fpo_2_s)
        self.assertEqual(assg_2_in.expression, 2)

        # Test 6 - A wire can connect a child output port to multiple child input ports and no
        # output ports, in which case the wire symbol is the source
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("fpo_0.r", ["fpo_1.s", "fpo_2.s"]), 
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"fpo_0.r", "fpo_1.r", "fpo_2.r", "fpo_0.s"})

        assg_0 = compiled.internal_parameter_assignments["fpo_0.r"]
        assg_0_in = compiled.internal_parameter_assignments["fpo_0.s"]
        assg_1 = compiled.internal_parameter_assignments["fpo_1.r"]
        assg_2 = compiled.internal_parameter_assignments["fpo_2.r"]

        fpo_0_s, fpo_0_r = sym.symbols("fpo_0.s, fpo_0.r")
        self.assertEqual(assg_0.expression, fpo_0_s)
        self.assertEqual(assg_1.expression, 2*fpo_0_r)
        self.assertEqual(assg_2.expression, 3*fpo_0_r)
        self.assertEqual(assg_0_in.expression, 2)

        # Test 7 - A wire can connect a child output port to multiple child input ports and
        # an output port, in which case the wire symbol is the output port symbol
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("fpo_0.r", ["fpo_1.s", "fpo_2.s", "s"]), 
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"fpo_1.r", "fpo_2.r", "fpo_0.s"})
        self.assertEqual(compiled.output_ports.keys(), {"s"})

        assg_0_in = compiled.internal_parameter_assignments["fpo_0.s"]
        assg_1 = compiled.internal_parameter_assignments["fpo_1.r"]
        assg_2 = compiled.internal_parameter_assignments["fpo_2.r"]

        assg_s = compiled.output_ports["s"].assignment

        s, fpo_0_s = sym.symbols("s, fpo_0.s")
        self.assertEqual(assg_1.expression, 2*s)
        self.assertEqual(assg_2.expression, 3*s)
        self.assertEqual(assg_0_in.expression, 2)

        self.assertEqual(assg_s.expression, fpo_0_s)

        # Test 8 - As test 7 but with another wire connecting input "fpo_0.s" to input port "a"
        cpo = CompositePortedObject(
            name="cpo",
            children=fpos,
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", "fpo_0.s"),
                ("fpo_0.r", ["fpo_1.s", "fpo_2.s", "s"]), 
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"fpo_1.r", "fpo_2.r"})
        self.assertEqual(compiled.output_ports.keys(), {"s"})

        assg_1 = compiled.internal_parameter_assignments["fpo_1.r"]
        assg_2 = compiled.internal_parameter_assignments["fpo_2.r"]

        assg_s = compiled.output_ports["s"].assignment

        s, a = sym.symbols("s, a")
        self.assertEqual(assg_1.expression, 2*s)
        self.assertEqual(assg_2.expression, 3*s)

        self.assertEqual(assg_s.expression, a)

    def test_cpo_compile_directed_nesting(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            assignments=[("r", "2*s")]
        )

        cpo_inner = CompositePortedObject(
            name="cpo_inner",
            children=[fpo],
            input_ports=["a"],
            output_ports=["b"],
            directed_wires=[
                ("a", "fpo.s"),
                ("fpo.r", "b"),
            ]
        )

        cpo_outer = CompositePortedObject(
            name="cpo_outer",
            children=[cpo_inner],
            input_ports=[("x", 1)],
            output_ports=["y"],
            directed_wires=[
                ("x", "cpo_inner.a"),
                ("cpo_inner.b", "y")
            ]
        )

        compiled = cpo_outer.compile()

        self.assertEqual(compiled.internal_parameter_assignments, {})
        self.assertEqual(compiled.output_ports.keys(), {"y"})

        assg = compiled.output_ports["y"].assignment
        self.assertEqual(assg.expression, 2*sym.Symbol("x"))

    def test_cpo_compile_port_forwarding(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            assignments=[("a", "2*b")],
        )

        cpo = CompositePortedObject(
            name="cpo",
            children=[fpo],
            input_ports=[("s", 1)],
        )

        # Port "b" of "fpo" is not connected and has no default value. Expect wiring error:
        with self.assertRaises(WiringError):
            cpo.compile()

        # With a default value at "b", no wiring error should be raised.
        fpo.input_ports["b"].default_value = 1
        cpo = CompositePortedObject(
            name="cpo",
            children=[fpo],
            input_ports=[("s", 1)],
        )
        cpo.compile()

        # Instead, port "b" of "fpo" is connected with no default value. Compile should run without error.   
        fpo.input_ports["b"].default_value = None     
        cpo = CompositePortedObject(
            name="cpo",
            children=[fpo],
            input_ports=[("s", 1)],
            directed_wires=[("s", "fpo.b")],
        )

        cpo.compile()


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

        compiled._set_input_parameters()
        
        self.assertIn("x", compiled.internal_parameter_assignments)
        assg = compiled.internal_parameter_assignments["x"]

        self.assertNotIn("x", compiled.required_inputs)

        self.assertIsInstance(assg, DefaultParameterAssignment)
        self.assertEqual(assg.expression, 10)

    def test_required_input_creation(self):
        fpo = FunctionalPortedObject(
            name="func_test",
            assignments=[("y", "2*x")],
        )

        compiled = fpo.compile()   

        self.assertIn("x", compiled.input_ports)

        compiled._set_input_parameters()

        self.assertNotIn("x", compiled.internal_parameter_assignments)
        self.assertIn("x", compiled.required_inputs)     

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

    def test_single_variable_compile(self):
        vpo = VariablePortedObject(
            name="vpo_test",
            assignments=[("y", "0.5*x")]
        )
        
        compiled = vpo.compile()
        self.assertIn("y", compiled.variable_ports)
        port = compiled.variable_ports["y"]
        self.assertEqual(port.assignment.expression, 0.5 * sym.Symbol("x"))

    def test_unexposed_variable(self):
        vpo = VariablePortedObject(
            name="second_order", 
            variable_ports=["y"],
            assignments=[("y", "0.1*x"), ("x", "y")],
        )
        # ODE: y'' = 0.1y

        compiled = vpo.compile()
        self.assertIn("x", compiled.internal_variable_assignments)
        assg = compiled.internal_variable_assignments["x"]
        self.assertEqual(assg.expression, sym.Symbol("y"))

        self.assertIn("y", compiled.variable_ports)
        assg = compiled.variable_ports["y"].assignment
        self.assertEqual(assg.expression, 0.1 * sym.Symbol("x"))

class TestCompositePortedObjects(unittest.TestCase):
    def test_port_behaviour_forwarding(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            assignments=[("r", "2*s")],
        )

        vpo = VariablePortedObject(
            name="vpo",
            assignments=[("x", "t*x")],
        )

        cpo = CompositePortedObject(
            name="cpo",
            children=[fpo, vpo],
            input_ports=[("a", 1), ("b", 1)],
            output_ports=["c"],
            variable_ports=["y"],
            directed_wires=[
                ("a", "fpo.s"),
                ("b", "vpo.t"),
                ("fpo.r", "c"),
            ],
            variable_wires=[
                (["vpo.x"], "y"),
            ]
        )

        compiled = cpo.compile()

        y, a, b = sym.symbols("y, a, b")

        # The variable assignment "t*x" at "vpo.x" should pass to the assignment "b*y" at "y"
        self.assertIn("y", compiled.variable_ports)
        assg = compiled.variable_ports["y"].assignment
        self.assertEqual(assg.expression, b*y)

        # The functional assignment "2*s" at "fpo.r" should pass to the assignment "2*a" at "c"
        self.assertIn("c", compiled.output_ports),
        assg = compiled.output_ports["c"].assignment
        self.assertEqual(assg.expression, 2*a)

    def test_variable_composition(self):
        vpo_1 = VariablePortedObject(
            name="vpo_1",
            input_ports=[("r_1", 2)],
            assignments=[("x", "r_1 * x")]
        )

        vpo_2 = VariablePortedObject(
            name="vpo_2",
            input_ports=[("r_2", 2)],
            assignments=[("x", "-r_2*x")]
        )

        cpo = CompositePortedObject(
            name="cpo",
            children=[vpo_1, vpo_2],
            variable_ports=["x"],
            variable_wires=[(["vpo_1.x", "vpo_2.x"], "x")],
        )

        self.assertEqual(len(cpo.variable_aggregation_wiring), 1)
        wire = cpo.variable_aggregation_wiring[0]
        self.assertEqual(wire.child_ports, ["vpo_1.x", "vpo_2.x"])
        self.assertEqual(wire.parent_port, "x")

        compiled = cpo.compile()
        # Check that the assignment at variable port x is x' = (vpo_1.r_1 - vpo_2.r_2)*x
        self.assertIn("x", compiled.variable_ports)
        port = compiled.variable_ports["x"]
        assg = port.assignment
        x, r_1, r_2 = sym.symbols("x, vpo_1.r_1, vpo_2.r_2")
        self.assertEqual(sym.simplify(assg.expression - (r_1-r_2)*x),0)

        # Also check that the default parameters were carried through
        self.assertIn("vpo_1.r_1", compiled.internal_parameter_assignments)
        self.assertIn("vpo_2.r_2", compiled.internal_parameter_assignments)

    def test_internal_composition(self):
        vpos = [
            VariablePortedObject(
                name=f"vpo_{i}",
                assignments=[
                    ("x", "-0.5*x"),
                    ("y", "0.5*x")
                ]
            )
            for i in range(2)
        ]

        cpo = CompositePortedObject(
            name="cpo",
            children=vpos,
            variable_wires=[
                {
                    "child_ports": ["vpo_0.y", "vpo_1.x"],
                    "output_name": "internal",
                }
            ]
        )

        self.assertEqual(len(cpo.variable_aggregation_wiring), 1)
        wire = cpo.variable_aggregation_wiring[0]
        self.assertEqual(wire.child_ports, ["vpo_0.y", "vpo_1.x"])
        self.assertEqual(wire.output_name, "internal")

        compiled = cpo.compile()
        # Check that the internal assignment is correct
        self.assertIn("internal", compiled.internal_variable_assignments)
        assg_1 = compiled.internal_variable_assignments["internal"]

        self.assertIn("vpo_0.x", compiled.internal_variable_assignments)
        assg_2 = compiled.internal_variable_assignments["vpo_0.x"]

        self.assertIn("vpo_1.y", compiled.internal_variable_assignments)
        assg_3 = compiled.internal_variable_assignments["vpo_1.y"]

        internal, vpo_0_x = sym.symbols("internal, vpo_0.x")

        self.assertEqual(assg_1.expression, -0.5*internal + 0.5*vpo_0_x)
        self.assertEqual(assg_2.expression, -0.5*vpo_0_x)
        self.assertEqual(assg_3.expression, 0.5*internal)

    def test_identical_internal_variables(self):
        vpos = [
            VariablePortedObject(
                name=f"vpo_{i}",
                variable_ports=["x"],
                input_ports=[("r", i)],
                assignments=[("x", "r*y"), ("y", "2*x")],
            )
            for i in range(2)
        ]

        cpo = CompositePortedObject(
            name="cpo",
            children=vpos,
            variable_wires=[
                {
                    "child_ports": ["vpo_0.x", "vpo_1.x"],
                    "output_name": "internal",
                }
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.internal_variable_assignments.keys(), {"vpo_0.y", "vpo_1.y", "internal"})
        assg_1 = compiled.internal_variable_assignments["vpo_0.y"]
        assg_2 = compiled.internal_variable_assignments["vpo_1.y"]
        assg_3 = compiled.internal_variable_assignments["internal"]

        vpo_0_y, vpo_1_y, vpo_0_r, vpo_1_r, internal = sym.symbols("vpo_0.y, vpo_1.y, vpo_0.r, vpo_1.r, internal")

        self.assertEqual(assg_1.expression, 2*internal)
        self.assertEqual(assg_2.expression, 2*internal)
        self.assertEqual(assg_3.expression, vpo_0_r*vpo_0_y + vpo_1_r*vpo_1_y)

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"vpo_0.r", "vpo_1.r"})
        assg_1 = compiled.internal_parameter_assignments["vpo_0.r"]
        assg_2 = compiled.internal_parameter_assignments["vpo_1.r"]

        self.assertEqual(assg_1.expression, 0)
        self.assertEqual(assg_2.expression, 1)


    def test_exposed_variable_renaming(self):
        vpos = [
            VariablePortedObject(
                name=f"vpo_{i}",
                assignments=[
                    ("x", "-0.5*x"),
                    ("y", "0.5*x")
                ]
            )
            for i in range(2)
        ]

        cpo = CompositePortedObject(
            name="cpo",
            children=vpos,
            variable_ports=["flow_in", "flow_mid", "flow_out"],
            variable_wires=[
                (["vpo_0.x"], "flow_in"),
                (["vpo_0.y", "vpo_1.x"], "flow_mid"),
                (["vpo_1.y"], "flow_out")
            ]
        )

        compiled = cpo.compile()
        # All assignments stored at variable ports, none internally
        self.assertEqual(compiled.variable_ports.keys(), {"flow_in", "flow_mid", "flow_out"})
        self.assertEqual(compiled.internal_variable_assignments, {})

        assg_in = compiled.variable_ports["flow_in"].assignment
        assg_mid = compiled.variable_ports["flow_mid"].assignment  
        assg_out = compiled.variable_ports["flow_out"].assignment

        flow_in, flow_mid = sym.symbols("flow_in, flow_mid")

        self.assertEqual(assg_in.expression, -0.5*flow_in)
        self.assertEqual(assg_mid.expression, -0.5*flow_mid + 0.5*flow_in)
        self.assertEqual(assg_out.expression, 0.5*flow_mid)

    def test_variable_port_forwarding_composition(self):
        vpo_1 = VariablePortedObject(
            name="vpo_1",
            assignments=[("x_1", "0.5*x_1")],
        )

        cpo_1 = CompositePortedObject(
            name="cpo_1",
            children=[vpo_1],
            variable_ports=["x_1"],
            variable_wires=[(["vpo_1.x_1"], "x_1")]
        )

        vpo_2 = VariablePortedObject(
            name="vpo_2",
            assignments=[("x_2", "0.8*x_2")],
        )

        cpo_2 = CompositePortedObject(
            name="cpo_2",
            children=[cpo_1, vpo_2],
            variable_ports=["x"],
            variable_wires=[(["cpo_1.x_1", "vpo_2.x_2"], "x")]
        )

        compiled = cpo_2.compile()

        self.assertIn("x", compiled.variable_ports)
        assg = compiled.variable_ports["x"].assignment

        self.assertEqual(assg.expression, 1.3*sym.Symbol("x"))

    def test_read_from_variable_port(self):
        vpo = VariablePortedObject(
            name="vpo",
            assignments=[("x", "r*x")],
        )

        fpo = FunctionalPortedObject(
            name="fpo",
            assignments=[("a", "2*b")]
        )

        cpo = CompositePortedObject(
            name="cpo",
            children=[vpo, fpo],
            variable_ports=["x"],
            directed_wires=[
                ("vpo.x", "fpo.b"),
                ("fpo.a", "vpo.r"),
            ],
            variable_wires=[(["vpo.x"], "x")],
        )

        compiled = cpo.compile()

        self.assertIn("x", compiled.variable_ports)
        assg_var = compiled.variable_ports["x"].assignment

        self.assertIn("fpo.a", compiled.internal_parameter_assignments)
        assg_par = compiled.internal_parameter_assignments["fpo.a"]
        
        x, fpo_a = sym.symbols("x, fpo.a")
        # Check x' = fpo.a * x
        self.assertEqual(assg_var.expression, fpo_a*x)
        # Check fpo.a = 2*x
        self.assertEqual(assg_par.expression, 2*x)

    def test_variable_port_read_and_composition(self):
        vpo_1 = VariablePortedObject(
            name="vpo_1",
            assignments=[("x", "2*x")],
        )

        vpo_2 = VariablePortedObject(
            name="vpo_2",
            assignments=[("y", "r*y")],
        )

        # Both the parameter r and the variable y are identified with x
        cpo = CompositePortedObject(
            name="cpo",
            children=[vpo_1, vpo_2],
            variable_ports=["x"],
            directed_wires=[("vpo_1.x", "vpo_2.r")],
            variable_wires=[(["vpo_1.x", "vpo_2.y"], "x")],
        )

        compiled = cpo.compile()

        self.assertIn("x", compiled.variable_ports)
        assg = compiled.variable_ports["x"].assignment

        x = sym.Symbol("x")
        self.assertEqual(assg.expression, 2*x + x**2)

    def test_functional_parameters(self):
        rate = FunctionalPortedObject(
            name="rate",
            assignments=[("a", "2*b")],
        )

        vpo_1 = VariablePortedObject(
            name="vpo_1",
            assignments=[("y", "0.5*y")],
        )

        vpo_2 = VariablePortedObject(
            name="vpo_2",
            assignments=[("x", "r*x")]
        )

        cpo = CompositePortedObject(
            name="cpo",
            children=[rate, vpo_1, vpo_2],
            variable_ports=["x","y"],
            directed_wires=[
                ("vpo_1.y", "rate.b"),
                ("rate.a", "vpo_2.r"),
            ],
            variable_wires=[
                (["vpo_1.y"], "y"),
                (["vpo_2.x"], "x")
            ]
        )

        compiled = cpo.compile()

        self.assertEqual(compiled.variable_ports.keys(), {"x", "y"})
        assg_x = compiled.variable_ports["x"].assignment
        assg_y = compiled.variable_ports["y"].assignment

        self.assertEqual(compiled.internal_parameter_assignments.keys(), {"rate.a"})
        assg_a = compiled.internal_parameter_assignments["rate.a"]

        x, y, rate_a = sym.symbols("x, y, rate.a")

        self.assertEqual(assg_x.expression, rate_a*x)
        self.assertEqual(assg_y.expression, 0.5*y)
        self.assertEqual(assg_a.expression, 2*y)



            













        






