import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from psymple.ported_objects import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
)
from psymple.system import System


##### Temperature model

temp = FunctionalPortedObject(
    name="temp",
    assignments=[("temp", "20*sin(2*pi*(T-100)/365) + 10")],
)

"""PREDATOR"""

##### Predator mortality #####

mort = FunctionalPortedObject(
    name="mort",
    assignments=[("function", "3/10")],  # 0.0001*temp**2 - 0.0005*temp + 0.01
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
        #("temp", "mort.temp"), 
        ("mort.function", "dyn.mort"),
        ],
    variable_wires=[(["dyn.n"], "n")],
)

"""---"""

"""PREY"""

##### Prey birth #####

birth = FunctionalPortedObject(
    name="birth",
    assignments=[
        ("function", "15/100")
    ],  # max(0,0.2 - (0.0001*temp**2 - 0.0005*temp + 0.005))
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
        #("temp", "birth.temp"), 
        ("birth.function", "dyn.birth"),
        ],
    variable_wires=[(["dyn.n"], "n")],
)

"""PREDATOR-PREY DYNAMICS"""

pred_prey = VariablePortedObject(
    name="pred_prey",
    input_ports=[
        dict(name="predation_rate", default_value=1/10 ),
        dict(name="predator_response_rate", default_value=1/10),
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
    variable_ports=["pred_n", "prey_n"],
    variable_wires=[
        (["pred.n", "pred_prey.pred"], "pred_n"),
        (["prey.n", "pred_prey.prey"], "prey_n"),
    ],
    directed_wires=[("temp.temp", "pred.temp"), ("temp.temp", "prey.temp")],
)

compiled = sys.compile()

print(compiled.variable_ports, compiled.internal_parameter_assignments)

var, par = compiled.get_assignments()
sys = System(variable_assignments=var, parameter_assignments=par)

print(var)

sys.variables["pred_n"].time_series = [50]
sys.variables["prey_n"].time_series = [100]


for var in sys.variables:
    print(f"d({var.symbol})/dT = {var.update_rule.equation}")

sys.simulate(t_end=365, n_steps=1000, mode="discrete")

sys.plot_solution({"pred_n", "prey_n"})
