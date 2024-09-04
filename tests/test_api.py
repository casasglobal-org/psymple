import unittest

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
)

from psymple.build.ports import (
    InputPort,
    OutputPort,
    VariablePort,
)

class TestAPI(unittest.TestCase):
    def test_ported_object_api_input_ports(self):
        X = CompositePortedObject("X")
        X.add_input_ports(
            InputPort("A", description="input port A", default_value=4),
            dict(name="B", default_value=2),
            "C",
        )
        names = [port.name for port in X.input_ports.values()]
        descriptions = [port.description for port in X.input_ports.values()]
        default_values = [port.default_value for port in X.input_ports.values()]
        self.assertEqual(names, ["A", "B", "C"])
        self.assertEqual(descriptions, ["input port A", "", ""])
        self.assertEqual(default_values, [4, 2, None])

    def test_ported_object_api_output_ports(self):
        X = CompositePortedObject("X")
        X.add_output_ports(
            OutputPort("A", description="output port A"),
            dict(name="B", description="output port B"),
            "C",
        )
        names = [port.name for port in X.output_ports.values()]
        descriptions = [port.description for port in X.output_ports.values()]
        self.assertEqual(names, ["A", "B", "C"])
        self.assertEqual(descriptions, ["output port A", "output port B", ""])

    def test_ported_object_api_variable_ports(self):
        X = CompositePortedObject("X")
        X.add_variable_ports(
            VariablePort("A", description="variable port A"),
            dict(name="B", description="variable port B"),
            "C",
        )
        names = [port.name for port in X.variable_ports.values()]
        descriptions = [port.description for port in X.variable_ports.values()]
        self.assertEqual(names, ["A", "B", "C"])
        self.assertEqual(descriptions, ["variable port A", "variable port B", ""])

    def test_ported_object_api_all_ports(self):
        X = CompositePortedObject(
            name="X",
            input_ports=[dict(name="A", description="input port A", default_value=4)],
            output_ports=[OutputPort("B", description="output port B")],
            variable_ports=["C"],
        )

        self.assertEqual(list(X.input_ports.keys()), ["A"])
        self.assertEqual(X.input_ports["A"].name, "A")
        self.assertEqual(X.input_ports["A"].description, "input port A")
        self.assertEqual(X.input_ports["A"].default_value, 4)

        self.assertEqual(list(X.output_ports.keys()), ["B"])
        self.assertEqual(X.output_ports["B"].name, "B")
        self.assertEqual(X.output_ports["B"].description, "output port B")

        self.assertEqual(list(X.variable_ports.keys()), ["C"])
        self.assertEqual(X.variable_ports["C"].name, "C")
        self.assertEqual(X.variable_ports["C"].description, "")

class TestDismantler(unittest.TestCase):
    def test_fpo_dismantler(self):
        fpo = FunctionalPortedObject(
            name="fpo",
            input_ports=[("a", 1), ("b", 2)],
            assignments=[("r", "a+b"), ("s", "a*b")],
            create_input_ports=False,
        )

        data = fpo.to_data()
        fpo_2 = data.to_ported_object()
        data_2 = fpo_2.to_data()

        self.assertEqual(data, data_2)

    def test_vpo_dismantler(self):
        vpo = VariablePortedObject(
            name="vpo",
            input_ports=[("r", 1), ("s", 2)],
            variable_ports=["x"],
            assignments=[("x", "r*y"), ("y", "s*x")],
            create_input_ports=False,
        )

        data = vpo.to_data()
        vpo_2 = data.to_ported_object()
        data_2 = vpo_2.to_data()

        self.assertEqual(data, data_2)

    def test_cpo_dismantler(self):
        vpos = [
            VariablePortedObject(
                name=f"vpo_{i}",
                input_ports=[("r", i+1), ("s", i+1)],
                variable_ports=["x"],
                assignments=[("x", "r*y"), ("y", "s*x")],
                create_input_ports=False
            )
            for i in range(5)
        ]

        fpos = [
            FunctionalPortedObject(
                name=f"fpo_{i}",
                input_ports=[("a", i+1), ("b", i+1)],
                assignments=[("r", "0.5*a"), ("s", "1.5*b")],
                create_input_ports=False,
            )
            for i in range(5)
        ]

        cpo_1 = CompositePortedObject(
            name="cpo_1",
            children=[fpos[0], fpos[1], vpos[0], vpos[1]],
            input_ports=["a", "b"],
            variable_ports=["x"],
            output_ports=["r", "s"],
            directed_wires=[
                ("a", "fpo_0.a"),
                ("b", "fpo_1.b"),
                ("fpo_0.r", "vpo_0.r"), 
                ("fpo_0.s", "vpo_0.s"),
                ("fpo_1.r", "r"),
                ("fpo_1.s", "s"),
            ],
            variable_wires=[(["vpo_0.x", "vpo_1.x"], "x")],
        )

        cpo_2 = CompositePortedObject(
            name="cpo_2",
            children=[cpo_1, fpos[2], vpos[2]],
            input_ports=["a"],
            output_ports=["r"],
            variable_ports=["x"],
            directed_wires=[
                ("a", "cpo_1.a"),
                ("fpo_2.s", "cpo_1.b"),
                ("fpo_2.r", "vpo_2.r"),
                ("cpo_1.s", "vpo_2.s"),
                ("cpo_1.r", "r"),
            ],
            variable_wires=[(["cpo_1.x", "vpo_2.x"], "x")]
        )

        cpo_3 = CompositePortedObject(
            name="cpo_3",
            children=[fpos[4], vpos[4]],
            input_ports=["a"],
            output_ports=["r"],
            variable_ports=["x"],
            directed_wires=[
                ("a", "fpo_4.a"),
                ("fpo_4.s", ["vpo_4.r", "vpo_4.s"]),
                ("fpo_4.r", "r"),
            ],
            variable_wires=[(["vpo_4.x"], "x")]
        )

        cpo_4 = CompositePortedObject(
            name="cpo_4",
            children=[cpo_3, vpos[3]],
            input_ports=["a", "b"],
            variable_ports=["x"],
            directed_wires=[
                ("a", "cpo_3.a"),
                ("b", ["vpo_3.r", "vpo_3.s"]),
            ],
            variable_wires=[(["cpo_3.x", "vpo_3.x"], "x")]
        )

        cpo_5 = CompositePortedObject(
            name="cpo_5",
            children=[cpo_4, cpo_2, fpos[3]],
            input_ports=[("a", 10)],
            variable_ports=["x"],
            output_ports=["s"],
            directed_wires=[
                ("a", "fpo_3.a"),
                ("cpo_2.r", ["cpo_4.a", "cpo_4.b"]),
                ("fpo_3.s", "s"),
                ("fpo_3.r", "cpo_2.a"),
            ],
            variable_wires=[(["cpo_2.x", "cpo_4.x"], "x")],
        )
    
        data = cpo_5.to_data()
        cpo_new = data.to_ported_object()
        data_new = cpo_new.to_data()

        self.assertEqual(data, data_new)

