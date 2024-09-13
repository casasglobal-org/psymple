import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    System,
)

S = System(
    system_parameters=[("G", 1)], #6.67
)

# VELOCITY

class force(FunctionalPortedObject):
    def __init__(self):
        super().__init__(
            name=f"force",
            assignments=[("mu", "G*m/d**3")]
        )

class vars(VariablePortedObject):
    def __init__(self):
        super().__init__(
            name="vars",
            assignments=[
                ("v_x", "mu * Del_x"),
                ("v_y", "mu * Del_y"),
            ]
        )

class dist(FunctionalPortedObject):
    def __init__(self):
        super().__init__(
            name="dist",
            assignments=[
                ("Del_x", "x_o - x"),
                ("Del_y", "y_o - y"),
                ("d", "sqrt((x_o-x)**2 + (y_o-y)**2)"),
            ]
        )

class velocity(CompositePortedObject):
    def __init__(self, id):
        super().__init__(
            name=f"velocity_{id}",
            children=[vars(), force(), dist()],
            input_ports=["x", "y", "x_o", "y_o", "m_o"],
            variable_ports=["v_x", "v_y"],
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
            ],
            variable_wires=[
                (["vars.v_x"], "v_x"),
                (["vars.v_y"], "v_y")
            ]
        )

class pos(VariablePortedObject):
    def __init__(self, id):
        super().__init__(
            name=f"pos_{id}",
            assignments=[
                ("x", "v_x"),
                ("y", "v_y"),
            ]
        )
    
n = 3

bodies = [i for i in range(1,n+1)]
ints = [f"{i}{j}" for i in range(1,n+1) for j in range(1,n+1) if i != j]
coords = ["x", "y"]

system = CompositePortedObject(
    name="system",
    children = [velocity(id) for id in ints] + [pos(i) for i in bodies],
    variable_ports=[port for i in bodies for port in [f"x_{i}", f"y_{i}", f"v_x_{i}", f"v_y_{i}"]],
    input_ports=[f"m_{i}" for i in bodies],
    directed_wires=[
        (f"m_{i}", [f"velocity_{j}{i}.m_o" for j in bodies if j != i])
        for i in bodies
    ]
    + [
        (
            f"pos_{i}.{coord}", 
            [f"velocity_{i}{j}.{coord}" for j in bodies if j != i]
            + [f"velocity_{j}{i}.{coord}_o" for j in bodies if j != i]
        )
        for i in bodies for coord in coords
    ]
    + [
        (f"velocity_{i}{i%n + 1}.v_{coord}", f"pos_{i}.v_{coord}")
        for i in bodies for coord in coords
    ],
    variable_wires=[
        (
            [f"velocity_{i}{j}.v_{coord}" for j in bodies if j != i], f"v_{coord}_{i}"
        )
        for i in bodies for coord in coords
    ]
    + [
        ([f"pos_{i}.{coord}"], f"{coord}_{i}")
        for i in bodies for coord in coords
    ],
)

S.set_object(system, compile=False)
S.compile()

print(S)

"""
initial_values={
    "x_1": 5.2,
    "y_1": 0,
    "x_2": 0,
    "y_2": 5.2,
    "x_3": -5.2,
    "y_3": 0,
    "v_x_1": 0,
    "v_y_1": 1,
    "v_x_2": -1,
    "v_y_2": 0,
    "v_x_3": 0,
    "v_y_3": -1,
},
"""

# Thse initial values should give 3-body figure eight motion
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

sim = S.create_simulation(
    #solver="discrete",
    initial_values=initial_values,
    input_parameters={
        "m_1": 1, #0.7
        "m_2": 1, #60
        "m_3": 1, #0.7
    }
)


sim.simulate(10)

sim.plot_solution()

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


#print(S)