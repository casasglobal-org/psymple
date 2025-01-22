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

"""
Setting up the system contextualisation
"""

frac_0 = lambda a,b,d: a/b if b != 0 else d

system = System()
system.add_system_parameter("g", "9.81"),
system.add_system_parameter("rho", "1.225")
system.add_utility_function(name="frac_0", function=frac_0)

"""
Vertical motion model
"""

v_gravity = VariablePortedObject( 
    name="v_gravity",
    assignments=[("v", "g"), ("x", "-v")], 
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
    input_ports=["C", "A", "m"],
    variable_ports=["v", "x"],
    directed_wires=[
        ("C", "f_drag.C"),
        ("A", "f_drag.A"),
        ("m", "f_drag.m"),
        ("f_drag.mu", "v_drag.mu"), 
    ],
    variable_wires=[
        (["v_gravity.v", "v_drag.v"], "v"),
        (["v_gravity.x"], "x"),
    ],
)   

"""
Vertical motion simulation
"""

system.set_object(model)

sim = system.create_simulation(
    initial_values = {"v": 0, "x": 200}, 
    input_parameters={"C": 1.1, "A": 0.2, "m": 2})
sim.simulate(t_end=10)

sim.plot_solution()

"""
Planar motion model
"""

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
    assignments=[("mu", "frac_0(1/2*coeff*rho*area,mass,0)")]
)

speed = FunctionalPortedObject(
    name="speed",
    assignments=[("s", "sqrt(v_x**2 + v_y**2)")]
)

model = CompositePortedObject(
    name="proj",
    children=[motion, drag, drag_magnitude, speed],
    input_ports=["C", "A", "m"],
    variable_ports=["pos_x", "pos_y", "vel_x", "vel_y"],
    directed_wires=[
        ("C", "drag_magnitude.coeff"),
        ("A", "drag_magnitude.area"),
        ("m", "drag_magnitude.mass"),
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

"""
Planar motion simulation
"""

system.set_object(model)

sim = system.create_simulation(
    initial_values ={"pos_x": 0, "pos_y": 200, "vel_x": 75, "vel_y": 15}, 
    input_parameters={"C": 1.1, "A": 0.2, "m": 2})
sim.simulate(t_end=10)
sim.plot_solution()

"""
Planar motion trajectory plot
"""

import matplotlib.pyplot as plt

pos_x = sim.variables["pos_x"].time_series
pos_y = sim.variables["pos_y"].time_series

plt.plot(pos_x, pos_y)
plt.grid()
plt.show()