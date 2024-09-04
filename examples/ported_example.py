import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    System,
)


##### Temperature model

temp = FunctionalPortedObject(
    name="temp",
    assignments=[("temp", "20*sin(2*pi*(T-100)/365) + 10")],
)

"""PREDATOR"""

##### Predator mortality #####

mort = FunctionalPortedObject(
    name="mort",
    assignments=[("function", "1")] #("function", "0.0001*temp**2 - 0.0005*temp + 0.01")],  3/10
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
        #("temp", ["mort.temp"]), 
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
    assignments=[("function", "T")]
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
    output_ports=["prey_birth"],
    directed_wires=[
        #("temp", ["birth_rate.temp"]), 
        ("birth_rate.function", ["dyn.birth", "prey_birth"]),
        ],
    variable_wires=[(["dyn.n"], "n")],
)

"""PREDATOR-PREY DYNAMICS"""

pred_prey = VariablePortedObject(
    name="pred_prey",
    input_ports=[
        dict(name="predation_rate"),
        dict(name="predator_response_rate", default_value=1),
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
    input_ports=[{"name": "predation_rate", "default_value": 4/3}],
    output_ports=["prey_birth"],
    variable_ports=["pred_n", "prey_n"],
    variable_wires=[
        (["pred.n", "pred_prey.pred"], "pred_n"),
        (["prey.n", "pred_prey.prey"], "prey_n"),
    ],
    directed_wires=[
        ("temp.temp", ["pred.temp", "prey.temp"]), 
        ("predation_rate", ["pred_prey.predation_rate"]),
        ("prey.prey_birth", ["prey_birth"]),
    ],
)

S = System(sys)

S.get_readout()

#sim = Simulation(S, solver="discrete_int")
import sympy as sym
T = sym.Symbol('T')
#from inspect import signature
#from time import time

vars_dict, pars_dict = S.get_readable_symbols()


S.compile()

sim_2 = S.create_simulation()
sim_2.set_initial_values({"pred_n": 1, "prey_n": 1})
sim_2.simulate(10, print_solve_time=True, n_steps=10000)
sim_2.plot_solution({"pred_n", "prey_n"})


sim = S.create_simulation(solver="continuous")
sim.set_initial_values({"pred_n": 1, "prey_n": 1})
sim.simulate(10, print_solve_time=True)
sim.plot_solution({"pred_n", "prey_n"})








#sim._compute_substitutions()

#for v in sim.variables.values():
#    v.update_rule.sub_symbols(vars_dict, pars_dict)
#    v.update_rule._lambdify()
#    print(v.update_rule._equation_lambdified.__code__.co_varnames)
    #print(v.update_rule.equation.subs(vars_dict|pars_dict))
    #print(v.update_rule.equation)



"""

#sim.set_initial_values({"pred_n": 5, "prey_n": 1000})
#sim.simulate(50, n_steps=400)

#sim.plot_solution({"pred_n", "prey_n"})


A = FunctionalPortedObject(
    "A",
    input_ports=[dict(name="mass", default_value=15)],
    assignments=[("area", "2*mass")],
)

B = FunctionalPortedObject(
    "B",
    input_ports=[dict(name="conv", default_value=0.092), dict(name="area", default_value=1)],
    assignments=[("index", "area/conv")],
)

C = FunctionalPortedObject(
    name="C",
    assignments=[("index", "2*LAI")],
)




LAI = CompositePortedObject(
    name="LAI",
    children=[A,B,C],
    output_ports=["LAI", "t_LAI"],
    directed_wires=[("A.area", ["B.area"]), 
                    ("B.index", ["LAI", "C.LAI"]),
                    ("C.index", ["t_LAI"])]
)

LAI_trigger = FunctionalPortedObject(
    name="LAI_trigger",
    assignments=[("ind", "Piecewise((1, LAI > 2), (0, True))")],
)

sys = CompositePortedObject(
    name="sys",
    children=[LAI, LAI_trigger],
    directed_wires=[("LAI.LAI", ["LAI_trigger.LAI"])],
)

S = System(LAI)

"""