import pathlib
import sys

from sympy import Symbol

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    System,
)

motion = VariablePortedObject(
    name="motion",
    assignments=[
        ("v_x", "0"),
        ("v_y", "-g"),
        ("pos_x", "v_x"),
        ("pos_y", "v_y"),
    ]
)

drag = VariablePortedObject(
    name="drag",
    assignments=[
        ("v_x", "-mu*v_x*s"),
        ("v_y", "-mu*v_y*s"),
    ]
)

drag_magnitude = FunctionalPortedObject(
    name="drag_magnitude",
    assignments=[("mu", "(coeff*air_density*area)/(2*mass)")]
)

speed = FunctionalPortedObject(
    name="speed",
    assignments=[("s", "sqrt(v_x**2 + v_y**2)")]
)

proj = CompositePortedObject(
    name="proj",
    children=[motion, drag, drag_magnitude, speed],
    input_ports=["coeff", "area", "mass"],
    variable_ports=["pos_x", "pos_y", "vel_x", "vel_y"],
    directed_wires=[
        ("coeff", "drag_magnitude.coeff"),
        ("area", "drag_magnitude.area"),
        ("mass", "drag_magnitude.mass"),
        ("drag_magnitude.mu", "drag.mu"),
        ("motion.v_x", "speed.v_x"),
        ("motion.v_y", "speed.v_y"),
        ("speed.s", "drag.s"),
    ],
    variable_wires=[
        (["motion.v_x", "drag.v_x"], "vel_x"),
        (["motion.v_y", "drag.v_y"], "vel_y"),
        (["motion.pos_x"], "pos_x"),
        (["motion.pos_y"], "pos_y"),
    ]
)

system = System()
system.add_system_parameter("g", "9.81"),
system.add_system_parameter("air_density", "1.225")
system.set_object(proj)

sim = system.create_simulation(
    solver="discrete", 
    initial_values={"pos_x": 0, "pos_y": 50, "vel_x": 3, "vel_y": 17},
    input_parameters={"coeff": 1, "area": 0.01, "mass": 2}      
)

sim.simulate(5, n_steps=1000)


import matplotlib.pyplot as plt 

plt.plot(sim.variables["pos_x"].time_series, sim.variables["pos_y"].time_series)
plt.show()

print(system)