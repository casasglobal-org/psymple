import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
)
from psymple.build import System

"""
Exponential population growth
"""

pop = VariablePortedObject(
    name="malthusian_pop",
    assignments=[("x", "r*x")],
    input_ports=[("r", 0.1)],
)

"""
Running the simulation 
"""

system_1 = System(pop)
system_1.compile()

sim_1 = system_1.create_simulation(initial_values={"x": 1})
sim_1.simulate(t_end=25)
sim_1.plot_solution()

"""
Changing parameters at simulation
"""

system_1 = System(pop)
system_1.compile()

sim_2 = system_1.create_simulation(
    initial_values={"x": 1}, 
    input_parameters={"r": 0.2}
)
sim_2.simulate(t_end=25)
sim_2.plot_solution()

"""
Overriding a default values with a function
"""

rate = FunctionalPortedObject(
    name="rate",
    assignments=[("r", "b-d")],
    input_ports=[("b", 0.4), ("d", 0.2)],
)

"""
Composing the function with the differential equation
"""

pop_system = CompositePortedObject(
    name="malthusian_pop_system",
    children=[pop, rate],
    directed_wires=[("rate.r", "malthusian_pop.r")],
)

"""
Exposing inputs
"""

pop_system = CompositePortedObject(
    name="malthusian_pop_system",
    children=[pop, rate],
    input_ports=[("b", 0.4), ("d", 0.2)],
    directed_wires=[
        ("rate.r", "malthusian_pop.r"),
        ("b", "rate.b"),
        ("d", "rate.d")
    ],
)

"""
Compilation and simulation
"""

system_2 = System(pop_system)
system_2.compile()

sim_3 = system_2.create_simulation(initial_values={"malthusian_pop.x": 1})
sim_3.simulate(t_end=25)
sim_3.plot_solution()

"""
Creating an interface
"""

pop_system = CompositePortedObject(
    name="malthusian_pop_system",
    children=[pop, rate],
    input_ports=[("b", 0.4), ("d", 0.2)],
    directed_wires=[
        ("rate.r", "malthusian_pop.r"),
        ("b", "rate.b"),
        ("d", "rate.d")
    ],
    variable_ports=["x"],
    variable_wires=[(["malthusian_pop.x"], "x")],
)