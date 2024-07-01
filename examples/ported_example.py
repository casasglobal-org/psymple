import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from psymple.ported_objects import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
)
from psymple.system import System, Simulation


##### Temperature model

temp = FunctionalPortedObject(
    name="temp",
    assignments=[("temp", "20*sin(2*pi*(T-100)/365) + 10")],
)

"""PREDATOR"""

##### Predator mortality #####

mort = FunctionalPortedObject(
    name="mort",
    assignments=[("function", "0.0001*temp**2 - 0.0005*temp + 0.01")],  # 3/10
)

##### Predator dynamics #####

pred_dyn = VariablePortedObject(
    name="dyn",
    assignments=[("n", "-mort*n")],
)

##### Predator functional population #####

pred = CompositePortedObject(
    name="pred",
    children=[mort, pred_dyn],
    variable_ports=["n"],
    input_ports=["temp"],
    directed_wires=[
        ("temp", ["mort.temp"]), 
        ("mort.function", ["dyn.mort"]),
        ],
    variable_wires=[(["dyn.n"], "n")],
)

"""---"""

"""PREY"""

##### Prey birth #####

birth = FunctionalPortedObject(
    name="birth",
    input_ports=[
        {"name": "min_birth_rate", "default_value": 0},
        {"name": "max_birth_rate", "default_value": 0.3},
        {"name": "birth_rate_coeff_1", "default_value": -0.0001},
        {"name": "birth_rate_coeff_2", "default_value": 0.0005},
        {"name": "birth_rate_coeff_3", "default_value": 0.295},
    ],
    assignments=[
        ("function", "max(min_birth_rate,max_birth_rate - (birth_rate_coeff_1*temp**2 - birth_rate_coeff_2*temp + birth_rate_coeff_3))"),
    ],  # 15/100
)

##### Birth #####

birth = FunctionalPortedObject(
    name="birth_rate",
    assignments=[("function", "1 - temp**2")]
)

##### Prey dynamics #####

prey_dyn = VariablePortedObject(
    name="dyn",
    assignments=[("n", "birth*n")],
)

##### Prey functional population #####

prey = CompositePortedObject(
    name="prey",
    children=[birth, prey_dyn],
    variable_ports=["n"],
    input_ports=["temp"],
    directed_wires=[
        ("temp", ["birth_rate.temp"]), 
        ("birth_rate.function", ["dyn.birth"]),
        ],
    variable_wires=[(["dyn.n"], "n")],
)

"""PREDATOR-PREY DYNAMICS"""

pred_prey = VariablePortedObject(
    name="pred_prey",
    input_ports=[
        dict(name="predation_rate"),
        dict(name="predator_response_rate", default_value=1/100000),
    ],
    assignments=[
        ("pred", "predator_response_rate*pred*prey"),
        ("prey", "-predation_rate*pred*prey"),
    ],
    
)

"""SYSTEM"""

sys = CompositePortedObject(
    name="system",
    children=[temp, pred, prey, pred_prey],
    input_ports=[{"name": "predation_rate", "default_value": 1/10}],
    variable_ports=["pred_n", "prey_n"],
    variable_wires=[
        (["pred.n", "pred_prey.pred"], "pred_n"),
        (["prey.n", "pred_prey.prey"], "prey_n"),
    ],
    directed_wires=[("temp.temp", ["pred.temp", "prey.temp"]), ("predation_rate", ["pred_prey.predation_rate"])],
)

S = System(sys)

#S.get_readout()

sim = Simulation(S, solver="discrete_int")


sim.set_initial_values({"pred_n": 5, "prey_n": 1000})
sim.simulate(50, n_steps=400)

sim.plot_solution({"pred_n", "prey_n"})



