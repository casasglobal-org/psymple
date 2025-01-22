import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    VariablePortedObject,
    System,
)

"""
Predator and prey components
"""

prey = VariablePortedObject(
    name="prey",
    assignments=[("x", "r*x")],
    input_ports=[("r", 0.4)],
)

pred = VariablePortedObject(
    name="pred",
    assignments=[("x", "r*x")],
    input_ports=[("r", -0.2)],
)

"""
Interaction
"""

interaction = VariablePortedObject(
    name="pred-prey",
    assignments=[("x", "r_1*x*y"), ("y", "r_2*x*y")],
    input_ports=[("r_1", -0.2), ("r_2", 0.1)],
)

"""
Ecosystem model
"""

ecosystem = CompositePortedObject(
    name="ecosystem",
    children=[pred, prey, interaction],
    variable_ports=["x", "y"],
    variable_wires=[
        (["prey.x", "pred-prey.x"], "x"),
        (["pred.x", "pred-prey.y"], "y"),
    ]
)

"""
Simulating the first model
"""

system = System(ecosystem, compile=True)

sim = system.create_simulation(initial_values={"x": 10, "y": 2})
sim.simulate(t_end=100)
sim.plot_solution()

"""
Logistic prey component
"""

pop = VariablePortedObject(
    name="pop",
    assignments=[("x", "r*x")],
)

limit = VariablePortedObject(
    name="limit",
    assignments=[("x", "- r/K* x**2")],
)

prey = CompositePortedObject(
    name="prey",
    children=[pop, limit],
    input_ports=[("r", 0.4), ("K", 10)],
    directed_wires=[
        ("r", ["pop.r", "limit.r"]), 
        ("K", "limit.K"),
    ],
    variable_ports = ["x"],
    variable_wires=[(["pop.x", "limit.x"], "x")],
)

"""
Simulating the second model
"""

ecosystem = CompositePortedObject(
    name="ecosystem",
    children=[pred, prey, interaction],
    variable_ports=["x", "y"],
    variable_wires=[
        (["prey.x", "pred-prey.x"], "x"),
        (["pred.x", "pred-prey.y"], "y"),
    ]
)

system = System(ecosystem, compile=True)

sim = system.create_simulation(initial_values={"x": 10, "y": 2})
sim.simulate(t_end=100)
sim.plot_solution()

"""
Tritrophic middle and apex predators
"""

pred_mid = VariablePortedObject(
    name="pred_mid",
    assignments=[("x", "r*x")],
    input_ports=[("r", -0.8)],
)

pred_apex = VariablePortedObject(
    name="pred_apex",
    assignments=[("x", "r*x")],
    input_ports=[("r", -0.05)],
)

"""
Tritrophic interactions
"""

int_prey_mid = VariablePortedObject(
    name="int_prey_mid",
    assignments=[("x", "r_1*x*y"), ("y", "r_2*x*y")],
    input_ports=[("r_1", -0.4), ("r_2", 0.3)],
)

int_mid_apex = VariablePortedObject(
    name="int_mid_apex",
    assignments=[("x", "r_1*x*y"), ("y", "r_2*x*y")],
    input_ports=[("r_1", -0.2), ("r_2", 0.1)],
)

"""
Tritrophic ecosystem
"""

ecosystem = CompositePortedObject(
    name="ecosystem",
    children=[prey, pred_mid, pred_apex, int_prey_mid, int_mid_apex],
    variable_ports=["x", "y", "z"],
    variable_wires=[
        (["prey.x", "int_prey_mid.x"], "x"),
        (["pred_mid.x", "int_prey_mid.y", "int_mid_apex.x"], "y"),
        (["pred_apex.x", "int_mid_apex.y"], "z")
    ]
)

"""
Simulating the tritrophic model
"""

system = System(ecosystem, compile=True)

sim = system.create_simulation(initial_values={"x": 10, "y": 5, "z": 2})
sim.simulate(t_end=100)
sim.plot_solution()