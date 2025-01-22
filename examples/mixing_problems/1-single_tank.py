import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    VariablePortedObject,
    System,
)

pipe_in = VariablePortedObject(
    name="pipe_in",
    assignments=[
        ("V", "r_0"),
        ("M", "r_0*c"),
    ],
)

pipe_out = VariablePortedObject(
    name="pipe_out",
    assignments=[
        ("V", "Piecewise((-r_1, V>V_m), (0, True))"), # (1)!
        ("M", "-r_1 * M/V"),
    ]
)

tank = CompositePortedObject(
    name="tank",
    children=[pipe_in, pipe_out],
    input_ports=["r_0", "r_1", "c", "V_m"],
    variable_ports=["V", "M"],
    variable_wires=[
        (["pipe_in.V", "pipe_out.V"], "V"),
        (["pipe_in.M", "pipe_out.M"], "M"),
    ],
    directed_wires=[
        ("r_0", "pipe_in.r_0"),
        ("r_1", "pipe_out.r_1"),
        ("c", "pipe_in.c"),
        ("V_m", "pipe_out.V_m"),
    ]
)

system = System(tank)
system.compile()

for name, inputs in zip(
    ["sim_1", "sim_2", "sim_3", "sim_4"], # (1)!
    [
        {"r_0": 4, "r_1": 4, "c": 0.5, "V_m": 10}, # (2)!
        {"r_0": 2, "r_1": 4, "c": 0.5, "V_m": 10},
        {"r_0": "4*sin(T) + 4", "r_1": 4, "c": 0.5, "V_m": 10},
        {"r_0": 4, "r_1": 4, "c": "0.5*sin(T) + 0.5", "V_m": 10},
    ]
):
    sim = system.create_simulation(
        name=name, 
        initial_values={"V": 1000, "M": 20}, # (3)!
        input_parameters=inputs,
    )
    sim.simulate(t_end=1000)

system.simulations["sim_1"].plot_solution({"M"})
system.simulations["sim_1"].plot_solution({"V"})