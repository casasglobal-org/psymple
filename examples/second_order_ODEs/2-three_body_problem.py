import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    System,
)

"""Common objects"""

vars = VariablePortedObject(
    name="vars",
    assignments=[
        ("v_x", "mu * Del_x"),
        ("v_y", "mu * Del_y"),
    ]
)

dist = FunctionalPortedObject(
    name="dist",
    assignments=[
        ("Del_x", "x_o - x"),
        ("Del_y", "y_o - y"),
        ("d", "sqrt((x_o-x)**2 + (y_o-y)**2)"),
    ]
)

force = FunctionalPortedObject(
    name=f"force",
    assignments=[("mu", "G*m/d**3")]
)

"""
Velocity model
"""

class velocity(CompositePortedObject):

    def __init__(self, id):
        super().__init__(
            name=f"velocity_{id}",
            children=[vars, force, dist],
            input_ports=["x", "y", "x_o", "y_o", "m_o"],
            variable_ports=["v_x", "v_y"],
            output_ports=["v_x", "v_y"],
            directed_wires=[
                ("m_o", "force.m"),
                ("x", "dist.x"),
                ("y", "dist.y"),
                ("x_o", "dist.x_o"),
                ("y_o", "dist.y_o"),
                ("dist.Del_x", "vars.Del_x"),
                ("dist.Del_y", "vars.Del_y"),
                ("dist.d", "force.d"),
                ("force.mu", "vars.mu"),
                ("vars.v_x", "v_x"),
                ("vars.v_y", "v_y"),
            ],
            variable_wires=[
                (["vars.v_x"], "v_x"),
                (["vars.v_y"], "v_y")
            ]
        )

"""
Trajectory model
"""

class pos(VariablePortedObject):
    def __init__(self, id):
        super().__init__(
            name=f"pos_{id}",
            assignments=[
                ("x", "v_x"),
                ("y", "v_y"),
            ]
        )


"""
System data
"""   

n=3

bodies = [f"{i+1}" for i in range(n)]
ints = [f"{i+1},{j+1}" for i in range(n) for j in range(n) if i != j]
coords = ["x", "y"]

"""
n-body model
"""

forces = [velocity(id) for id in ints]
positions = [pos(id) for id in bodies]

n_body_model = CompositePortedObject(
    name="system",
    children = forces + positions,
    variable_ports=[
        port 
        for i in bodies 
        for port in [f"x_{i}", f"y_{i}", f"v_x_{i}", f"v_y_{i}"]
    ],
    input_ports=[f"m_{i}" for i in bodies],
    directed_wires=[
        (f"m_{i}", [f"velocity_{j},{i}.m_o" for j in bodies if j != i])
        for i in bodies
    ]
    + [
        (
            f"pos_{i}.{coord}", 
            [f"velocity_{i},{j}.{coord}" for j in bodies if j != i]
            + [f"velocity_{j},{i}.{coord}_o" for j in bodies if j != i]
        )
        for i in bodies for coord in coords
    ]
    + [
        (f"velocity_{i},{int(i)%n + 1}.v_{coord}", f"pos_{i}.v_{coord}") # (1)!
        for i in bodies for coord in coords
    ],
    variable_wires=[
        (
            [f"velocity_{i},{j}.v_{coord}" for j in bodies if j != i], 
            f"v_{coord}_{i}"
        )
        for i in bodies for coord in coords
    ]
    + [
        ([f"pos_{i}.{coord}"], f"{coord}_{i}")
        for i in bodies for coord in coords
    ],
)

"""
System and context
"""

S = System(
    n_body_model,
    system_parameters=[("G", 1)],
    compile=True
)

"""
Initial conditions and input parameters
"""

initial_values={
    "x_1": 0.9700436,
    "y_1": -0.24308753,
    "x_2": 0,
    "y_2": 0,
    "x_3": -0.9700436,
    "y_3": 0.24308753,
    "v_x_1": 0.466203685,
    "v_y_1": 0.43236573,
    "v_x_2": -2*0.466203685,
    "v_y_2": -2*0.43236573,
    "v_x_3": 0.466203685,
    "v_y_3": 0.43236573,
}

input_parameters={
    "m_1": 1,
    "m_2": 1,
    "m_3": 1,
}

"""
Simulation and trajectory plot
"""

sim = S.create_simulation(
    initial_values=initial_values,
    input_parameters=input_parameters,
)

sim.simulate(t_end=10)

import matplotlib.pyplot as plt

x_1 = sim.variables["x_1"].time_series
y_1 = sim.variables["y_1"].time_series

x_2 = sim.variables["x_2"].time_series
y_2 = sim.variables["y_2"].time_series

x_3 = sim.variables["x_3"].time_series
y_3 = sim.variables["y_3"].time_series


plt.plot(x_1, y_1, color="blue")
plt.plot(x_2, y_2, color="red")
plt.plot(x_3, y_3, color="green")

plt.show()