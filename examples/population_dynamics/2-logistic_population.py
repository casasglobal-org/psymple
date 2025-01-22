import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    VariablePortedObject,
    System,
)

"""
Basic population model
"""

pop = VariablePortedObject(
    name="malthusian_pop",
    assignments=[("x", "r*x")],
    input_ports=[("r", 0.1)],
)

"""
Direct logistic implementation
"""

logistic_simple = VariablePortedObject(
    name="logistic_simple",
    assignments=[("x", "r*x*(1-x/K)")],
    input_ports=[("r", 0.1), ("K", 10)],
)

"""
Structural implementation
"""

limit = VariablePortedObject(
    name="limit",
    assignments=[("x", "- r/K* x**2")],
    input_ports=[("r", 0.1), ("K", 10)],
)

logistic_pop = CompositePortedObject(
    name="logistic_pop",
    children=[pop, limit],
    variable_ports = ["x"],
    variable_wires=[(["malthusian_pop.x", "limit.x"], "x")],
)

"""
Sharing input parameters
"""

logistic_pop = CompositePortedObject(
    name="logistic_pop",
    children=[pop, limit],
    input_ports=[("r", 0.1), ("K", 10)],
    directed_wires=[
        ("r", ["malthusian_pop.r", "limit.r"]), # (1)!
        ("K", "limit.K"),
    ],
    variable_ports = ["x"],
    variable_wires=[(["malthusian_pop.x", "limit.x"], "x")],
)

"""
System and simulation - checking implementations are the same
"""


system_1 = System(logistic_simple)
system_1.compile()

sim_1 = system_1.create_simulation(initial_values={"x": 1})
sim_1.simulate(t_end=100)
sim_1.plot_solution()


system_2 = System(logistic_pop)
system_2.compile()

sim_2 = system_2.create_simulation(initial_values={"x": 1})
sim_2.simulate(t_end=100)
sim_2.plot_solution()

