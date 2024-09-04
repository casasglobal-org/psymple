import unittest
import random

from psymple.abstract import ParsingError

from psymple.build.system import SystemError

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
    System, 
)

from psymple.build.ported_objects import (
    WiringError,
    DependencyError,
)

from psymple.variables import (
    SimVariable,
    SimParameter,
)

from numpy import sin, pi

from sympy import (
    sin as sym_sin,
    Symbol,
    Function,
    symbols,
)

RANDOM_SEED = 42

def temp(time):
    return 5*sin(2*pi*time)+10

def generate_test_pairs(func):
    random.seed(RANDOM_SEED)
    tests = [(x:=10*random.random(), func(x)) for i in range(20)]
    return tests

class TestSystemFunctions(unittest.TestCase):
    def test_system_parameter_callable(self):
        
        S = System(time_symbol="T")

        # Should fail because callable temp argument 'time' is not a system parameter
        with self.assertRaises(SystemError):
            S.add_system_parameter(name="temp", function=temp)

        # Now, "T" is the time symbol
        S.add_system_parameter(name="temp", function=temp, signature=("T",))

        # Check the function was added to system parameters correctly
        self.assertIn("temp", S.system_parameters)

        T = symbols("T")
        func = S.system_parameters["temp"]

        self.assertEqual(func.name, "temp")
        self.assertEqual(func.args, (T,))

        # Check the function was added to the lambdify namespace correctly
        self.assertIn({"temp": temp}, S.lambdify_ns)

    def test_system_parameter_symbolic(self):
        S = System(time_symbol="T")

        # Exception because "time" is not a system parameter or time symbol
        with self.assertRaises(SystemError):
            S.add_system_parameter("temp", "5*sin(2*pi*time)+10")

        S.add_system_parameter("temp", "5*sin(2*pi*T)+10")

        # Check the function was added to system parameters correctly
        self.assertIn("temp", S.system_parameters)

        T = symbols("T")
        func = S.system_parameters["temp"]

        self.assertEqual(func.name, "temp")
        self.assertEqual(func.args, (T,))

        # Check the function was added to the lambdify namespace correctly
        entry = next((entry for entry in S.lambdify_ns if "temp" in entry))
        self.assertIsNotNone(entry)
        func = entry["temp"]
        for x,y in generate_test_pairs(temp):
            self.assertAlmostEqual(func(x), y)

    def test_multiple_system_parameters(self):
        S = System()

        # These two calls reference undefined system parameters A and B
        with self.assertRaises(SystemError):
            S.add_system_parameter("C", "A+B")
            S.add_system_parameter("D", lambda A, B: 0 if B == 0 else A/B)

        # Add two independent parameters, one callable one symbolic
        S.add_system_parameter("A", "2")
        S.add_system_parameter("B", lambda x: x**2, signature=("T",))

        # Now the two parameters depending on A and B are added
        S.add_system_parameter("C", "A+B", signature=("A", "B"))
        S.add_system_parameter("D", lambda A, B: 0 if B == 0 else A/B, signature=("A", "B"))

        # Check the system paramters dictionary generated correctly
        self.assertEqual(S.system_parameters.keys(), {"A", "B", "C", "D"})

        # Check the lambdify callables function correctly
        funcs = {}
        for param in {"A", "B", "C", "D"}:
            entry = next((entry for entry in S.lambdify_ns if param in entry))
            self.assertIsNotNone(entry)
            funcs[param] = entry[param]
            
        func_A = funcs["A"]
        self.assertAlmostEqual(func_A(), 2)

        func_B = funcs["B"]
        for x, y in [(0,0), (1,1), (2,4), (3,9), (4,16)]:
            self.assertAlmostEqual(func_B(x),y)
        
        func_C = funcs["C"]
        for x,y in [(0,2), (1,3), (2,6), (3,11), (4,18)]:
            self.assertAlmostEqual(func_C(func_A(), func_B(x)),y)

        func_D = funcs["D"]
        for x, y in [(0, 0), (1, 2), (2, 1/2), (3, 2/9), (4, 2/16)]:
            self.assertAlmostEqual(func_D(func_A(), func_B(x)), y)

    def test_utility_function_callable(self):
        S = System(time_symbol="T")
        
        S.add_utility_function("temp", temp)

        self.assertIn("temp", S.utility_functions)
        # Utility functions should only contain a symbol representation of the function, without arguments
        self.assertEqual(S.utility_functions["temp"].name, "temp")

        self.assertIn({"temp": temp}, S.lambdify_ns)

    def test_utility_function_symbolic(self):
        S = System(time_symbol="T")

        S.add_utility_function("temp", "5*sin(2*pi*time)+10")
        self.assertIn("temp", S.utility_functions)
        # Utility functions should only contain a symbol representation of the function, without arguments
        self.assertEqual(S.utility_functions["temp"].name, "temp")

        entry = next((entry for entry in S.lambdify_ns if "temp" in entry))
        self.assertIsNotNone(entry)
        func = entry["temp"]
        for x,y in generate_test_pairs(temp):
            self.assertAlmostEqual(func(x), y)

    def test_signature_order_preservation(self):
        pass

class TestCompilation(unittest.TestCase):
    def test_add_ported_object(self):
        fpo = FunctionalPortedObject(
            name="rate",
            assignments=[("r", "2*a")],
        )

        vpo = VariablePortedObject(
            name="growth",
            assignments=[("x", "r*x")],
        )

        cpo = CompositePortedObject(
            name="species",
            children=[fpo, vpo],
            input_ports=[("a", 0.1)],
            variable_ports=["x"],
            directed_wires=[
                ("a", "rate.a"),
                ("rate.r", "growth.r"),
            ],
            variable_wires=[
                (["growth.x"], "x")
            ],
        )

        S = System(cpo)
        S.compile()
        
        x, rate_r, a = symbols("x, rate.r, a")

        self.assertEqual(S.variables.keys(), {x})
        self.assertEqual(S.parameters.keys(), {rate_r, a})

        var_x = S.variables[x]
        self.assertIsInstance(var_x, SimVariable)
        self.assertEqual(var_x.symbol, x)
        self.assertEqual(var_x.update_rule.expression, rate_r*x)

        par_r = S.parameters[rate_r]
        self.assertIsInstance(par_r, SimParameter)
        self.assertEqual(par_r.symbol, rate_r)
        self.assertEqual(par_r.value, 2*a)

        par_a = S.parameters[a]
        self.assertIsInstance(par_a, SimParameter)
        self.assertEqual(par_a.symbol, a)
        self.assertEqual(par_a.value, 0.1)

    def test_compile_at_child(self):
        fpo = FunctionalPortedObject(
            name="rate",
            assignments=[("r", "2*a")],
        )

        vpo = VariablePortedObject(
            name="growth",
            assignments=[("x", "r*x")],
        )

        cpo = CompositePortedObject(
            name="species",
            children=[fpo, vpo],
            input_ports=[("a", 0.1)],
            variable_ports=["x"],
            directed_wires=[
                ("a", "rate.a"),
                ("rate.r", "growth.r"),
            ],
            variable_wires=[
                (["growth.x"], "x")
            ],
        )

        S = System(cpo)
        a, r, rate_r, x = symbols("a r rate.r x")

        # Check compile with no argument returns the whole system
        S.compile()
        self.assertEqual(S.parameters.keys(), {a, rate_r})
        self.assertEqual(S.variables.keys(), {x})

        # Check "species" also returns the whole system
        S.compile("species")
        self.assertEqual(S.parameters.keys(), {a, rate_r})
        self.assertEqual(S.variables.keys(), {x})

        # Check "species.rate" returns just the object fpo
        S.compile("species.rate")
        self.assertEqual(S.parameters.keys(), {a, r})
        self.assertEqual(set(S.variables.keys()), set())

        # Check "rate" returns the same as "species.rate"
        S.compile("rate")
        self.assertEqual(S.parameters.keys(), {a, r})
        self.assertEqual(set(S.variables.keys()), set())

    def test_system_contextualisation_no_default(self):
        fpo = FunctionalPortedObject(
            name="rate",
            assignments=[("r", "2*temp")],
        )

        S = System()

        # With no context or default to "temp" in fpo, it should become a required input parameter.
        S.set_object(fpo)
        temp_param = S.parameters["temp"]
        self.assertEqual(temp_param.type, "required")

        # With "temp" defined as a system parameter, no input port or corresponding parameter will be
        # created.
        S.add_system_parameter("temp", temp, signature=("T",))
        S.set_object(fpo)

        with self.assertRaises(KeyError):
            temp_param = S.parameters["temp"]

    def test_system_contextualisation_with_default(self):
        fpo = FunctionalPortedObject(
            name="rate",
            input_ports=[("temp", 10)],
            assignments=[("r", "2*temp")],
        )

        S = System()

        # With fpo providing a default to "temp", system will compile and it will become a default_optional
        # parameter.
        S.set_object(fpo)
        temp_param = S.parameters["temp"]
        self.assertEqual(temp_param.type, "default_optional")

        # With a system parameter temp, a warning should be raised because of the name conflit, and the
        # port temp overwritten by the parameter
        S.add_system_parameter("temp", temp, signature=("T",))
        with self.assertWarns(Warning):
            S.set_object(fpo)

        with self.assertRaises(KeyError):
            temp_param = S.parameters["temp"]

class TestParameters(unittest.TestCase):
    def test_set_parameters(self):
        fpo = FunctionalPortedObject(
            name="rate",
            input_ports=[("b", 1)],
            assignments=[("r", "2*a*b")],
        )

        vpo = VariablePortedObject(
            name="growth",
            input_ports=[("r", 1)],
            assignments=[("x", "r*x")],
        )

        cpo = CompositePortedObject(
            name="species",
            children=[fpo, vpo],
            input_ports=["a"],
            variable_ports=["x"],
            directed_wires=[
                ("a", "rate.a"),
                ("rate.r", "growth.r"),
            ],
            variable_wires=[
                (["growth.x"], "x")
            ],
        )

        S = System(cpo, compile=True)

        param_r = S.parameters["rate.r"]
        param_b = S.parameters["rate.b"]
        param_a = S.parameters["a"]

        # Initial parameter types
        self.assertEqual(param_r.type, "functional")
        self.assertEqual(param_b.type, "default_exposable")
        self.assertEqual(param_a.type, "required")

        # Initial parameter values
        self.assertEqual(param_b.value, 1)
        self.assertEqual(param_a.value, None)

        # We can't update "rate.r" because it is defined with a wire
        with self.assertRaises(TypeError):
            S.set_parameters({"rate.r": 21})

        # We can update both "rate.b" and "a"
        S.set_parameters({"rate.b": 2, "a": 3})
        self.assertEqual(param_b.value, 2)
        self.assertEqual(param_a.value, 3)

        # Both should now be default_optional parameters
        self.assertEqual(param_b.type, "default_optional")
        self.assertEqual(param_a.type, "default_optional")

        # Set using a float
        S.set_parameters({"rate.b": 3.1})
        self.assertEqual(param_b.value, 3.1)

        # Set using a str
        S.set_parameters({"rate.b": "3.2"})
        self.assertEqual(param_b.value, 3.2)

        # Set using not a str, int or float
        with self.assertRaises(TypeError):
            S.set_parameters({"rate.b": dict(a=2)})

        # Set using a function of time
        S.set_parameters({"rate.b": "sin(T)"})
        self.assertEqual(param_b.value, sym_sin(Symbol("T")))

        # Set using a system parameter "TEMP" which isn't defined
        with self.assertRaises(ParsingError):
            S.set_parameters({"rate.b": "TEMP"})

        # Add the system parameter "TEMP" and try again
        S.add_system_parameter("TEMP", temp, ("T",))
        S.set_parameters({"rate.b": "TEMP"})
        function = S.system_parameters["TEMP"]
        self.assertEqual(param_b.value, function)

    def test_parameter_update_order(self):
        fpos = [
            FunctionalPortedObject(
                name=f"function_{i}",
                assignments=[("r", "2*a")],
            )
            for i in range(1,4)
        ]

        cpo = CompositePortedObject(
            name="system",
            children=fpos,
            input_ports=["a"],
            output_ports=["r"],
            directed_wires=[
                ("a", "function_1.a"),
                ("function_1.r", "function_2.a"),
                ("function_2.r", "function_3.a"),
                ("function_3.r", "r"),
            ],
        )

        S = System(cpo, compile=True)

        order = [p.name for p in S.compute_parameter_update_order()]

        self.assertEqual(order, ["a", "function_1.r", "function_2.r", "r"])

    def test_cyclic_dependencies(self):
        fpos = [
            FunctionalPortedObject(
                name=f"function_{i}",
                assignments=[("r", "2*a")],
            )
            for i in range(1,4)
        ]

        cpo = CompositePortedObject(
            name="system",
            children=fpos,
            directed_wires=[
                ("function_1.r", "function_2.a"),
                ("function_2.r", "function_3.a"),
                ("function_3.r", "function_1.a")
            ],
        )

        S = System(cpo, compile=True)

        # Example has cyclic dependencies and should raise an exception
        with self.assertRaises(SystemError):
            S.compute_parameter_update_order()

class TestCreteSimulation(unittest.TestCase):
    def test_create_system(self):
        vpo = VariablePortedObject(
            name="growth",
            input_ports=[("r", 1)],
            assignments=[("x", "r*x")],
        )

        S = System(vpo, compile=True)

        # With no name provided, simulation is not stored
        S.create_simulation() 
        self.assertEqual(S.simulations, {})

        # With a name provided, simulation is stored
        sim = S.create_simulation("sim")
        self.assertEqual(S.simulations.keys(), {"sim"})
        self.assertEqual(S.simulations["sim"], sim)

        









        

        