import unittest

from sympy import symbols

from psymple.build import (
    VariablePortedObject,
    FunctionalPortedObject,
    CompositePortedObject,
    System,
)

from psymple.simulate import Simulation

v_gravity = VariablePortedObject(
    name="v_gravity",
    assignments=[("v", "g")],
)

v_drag = VariablePortedObject(
    name="v_drag",
    assignments=[("v", "-mu * v**2")], 
)

f_drag = FunctionalPortedObject(
    name="f_drag",
    assignments=[("mu", "frac_0(1/2 * C * rho * A, m, 0)")], 
)

model = CompositePortedObject(
    name="model",
    children=[v_gravity, v_drag, f_drag], 
    input_ports=["C", "rho", "A", "m"], 
    variable_ports=["v"], 
    directed_wires=[
        ("C", "f_drag.C"), 
        ("rho", "f_drag.rho"),
        ("A", "f_drag.A"),
        ("m", "f_drag.m"),
        ("f_drag.mu", "v_drag.mu"), 
    ],
    variable_wires=[
        (["v_gravity.v", "v_drag.v"], "v") 
    ],
)

S = System(model)
S.add_system_parameter("g", 9.81)
S.add_utility_function("frac_0", lambda a,b,d: a/b if b != 0 else d)
S.compile()

class TestSimulationMethods(unittest.TestCase):
    def test_create_simulation(self):
        sim = Simulation(S)

        self.assertEqual(sim.solver, "continuous")
        # Variables and parameters should be copies
        self.assertNotEqual(sim.variables, S.variables)
        self.assertNotEqual(sim.parameters, S.parameters)

    def test_create_multiple_simulations(self):
        S.create_simulation("sim_1", "continuous", initial_values={"v": 1}, input_parameters={"C": 1.1, "rho": 1, "A": 0.2, "m": 2})
        S.create_simulation("sim_2", "discrete", initial_values={"v": 0}, input_parameters={"C": 2.1, "rho": 2, "A": 0.4, "m": 4})

        self.assertEqual(S.simulations.keys(), {"sim_1", "sim_2"})
        sim_1 = S.simulations["sim_1"]
        sim_2 = S.simulations["sim_2"]

        self.assertNotEqual(sim_1.variables, sim_2.variables)
        self.assertNotEqual(sim_1.parameters, sim_2.parameters)

        self.assertEqual(sim_1.variables["v"].initial_value, 1)
        self.assertEqual(sim_2.variables["v"].initial_value, 0)

        syms = symbols(["C", "rho", "A", "m"])

        self.assertEqual([p.value for name, p in sim_1.parameters.items() if name in syms], [1.1, 1, 0.2, 2])
        self.assertEqual([p.value for name, p in sim_2.parameters.items() if name in syms], [2.1, 2, 0.4, 4])

    def test_discrete_simulator(self):
        sim = S.create_simulation("discrete", initial_values={"v": 0}, input_parameters={"C": 1.1, "rho": 1, "A": 0.2, "m": 2})
        sim.simulate(t_end=10, n_steps=100)

        final_v_value = sim.variables["v"].time_series[-1]

        self.assertAlmostEqual(final_v_value, 13.35, 2)

    def test_continuous_simulator(self):
        sim = S.create_simulation(initial_values={"v": 0}, input_parameters={"C": 1.1, "rho": 1, "A": 0.2, "m": 2})
        sim.simulate(t_end=10)

        final_v_value = sim.variables["v"].time_series[-1]

        self.assertAlmostEqual(final_v_value, 13.35, 2)


