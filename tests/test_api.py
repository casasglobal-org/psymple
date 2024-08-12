import unittest

from psymple.ported_objects import (
    CompositePortedObject,
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