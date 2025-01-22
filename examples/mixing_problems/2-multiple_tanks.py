import pathlib
import sys

from sympy import Symbol

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    VariablePortedObject,
    System,
)

"""
System data
"""

# Number of tanks
n = 2

# List of tanks created
tanks_id = [i for i in range(1, n + 1)]

# List of pipes between tanks eg. (1,2) is a pipe from tank 1 to tank 2
link_pipes_id = [(i, j) for i in range(1, n + 1) for j in range(1, n + 1) if j != i]

# List of tanks with an external pipe in
pipes_in_id = [1, 2]

# List of tanks with an external pipe out
pipes_out_id = [1, 2]

"""
Flow building blocks
"""

pipes_in = [
    VariablePortedObject(
        name=f"in_{i}",
        assignments=[
            ("Q_in", "rate * conc"),
            ("V_in", "rate"),
        ],
    )
    for i in pipes_in_id
]

pipes_out = [
    VariablePortedObject(
        name=f"out_{i}",
        assignments=[
            ("Q_out", "-rate * Q_out / V_out"), 
            ("V_out", "-rate")
        ],
    )
    for i in pipes_out_id
]

connectors = [
    VariablePortedObject(
        name=f"pipe_{i}_{j}",
        assignments=[
            ("Q_in", "- rate * Q_in / V_in"),
            ("Q_out", "rate * Q_in / V_in"),
            ("V_in", "-rate"),
            ("V_out", "rate"),
        ],
    )
    for i, j in link_pipes_id
]

"""
Model of the tanks by aggregation
"""

tanks = CompositePortedObject(
    name="tanks",
    children=pipes_in + pipes_out + connectors,
    variable_ports=[f"Q_{i}" for i in tanks_id]
    + [f"V_{i}" for i in tanks_id],
    input_ports=[f"rate_{i}_{j}" for i, j in link_pipes_id]
    + [f"conc_in_{i}" for i in pipes_in_id]
    + [f"rate_in_{i}" for i in pipes_in_id]
    + [f"rate_out_{i}" for i in pipes_out_id],
    directed_wires=[
        (f"rate_{i}_{j}", f"pipe_{i}_{j}.rate")
        for i, j in link_pipes_id
    ]
    + [(f"conc_in_{i}", f"in_{i}.conc") for i in pipes_in_id]
    + [(f"rate_out_{i}", f"out_{i}.rate") for i in pipes_out_id]
    + [(f"rate_in_{i}", f"in_{i}.rate") for i in pipes_in_id],
    variable_wires=[
        (
            ([f"in_{i}.Q_in"] if i in pipes_in_id else [])
            + ([f"out_{i}.Q_out"] if i in pipes_out_id else [])            
            + [f"pipe_{j}_{i}.Q_out" for j in tanks_id if j != i]
            + [f"pipe_{i}_{j}.Q_in" for j in tanks_id if j != i],
            f"Q_{i}",
        )
        for i in tanks_id
    ]
    + [
        (
            ([f"in_{i}.V_in"] if i in pipes_in_id else [])
            + ([f"out_{i}.V_out"] if i in pipes_out_id else [])
            + [f"pipe_{j}_{i}.V_out" for j in tanks_id if j != i]
            + [f"pipe_{i}_{j}.V_in" for j in tanks_id if j != i],
            f"V_{i}",
        )
        for i in tanks_id
    ],
)

"""
Compilation and simulation
"""

S = System(tanks)
S.compile()

S.set_parameters(
    {
        "rate_1_2": 3,
        "rate_2_1": 10,
        "rate_in_1": "Piecewise((4, T<50), (0, True))",
        "rate_in_2": 7,
        "conc_in_1": 0.5,
        "conc_in_2": 0,
        "rate_out_1": 11,
        "rate_out_2": 0,
    }
)

print(S)

sym = S.create_simulation(
    initial_values={"Q_1": 20, "Q_2": 80, "V_1": 800, "V_2": 1000}
)

sym.simulate(t_end=250)

sym.plot_solution()
