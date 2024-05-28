import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import sympy as sym

from psymple.ported_objects import (
    CompiledPort,
    CompositePortedObject,
    DifferentialAssignment,
    VariableAggregationWiring,
    VariablePort,
    VariablePortedObject,
    InputPort,
)
from psymple.system import System
from psymple.variables import (
    # Parameters,
    # SimParameter,
    # SimUpdateRule,
    SimVariable,
    Variable,
    Variables,
)

rabbits = Variable("rabbits", 10)
# assg = DifferentialAssignment(rabbits, sym.sympify("r_growth") * sym.sympify("rabbits"))
assg = DifferentialAssignment(rabbits, 1.1 * sym.sympify("rabbits"))
rabbit_growth = VariablePortedObject("rabbit growth", [assg])
# rabbit_growth.add_input_port(InputPort("r_growth", default_value=1.1))

foxes = Variable("foxes", 5)
assg = DifferentialAssignment(foxes, -0.4 * sym.sympify("foxes"))
fox_growth = VariablePortedObject("fox growth", [assg])

rabbits = Variable("rabbits", 10)
foxes = Variable("foxes", 5)
assg1 = DifferentialAssignment(
    rabbits, -0.4 * sym.sympify("foxes") * sym.sympify("rabbits")
)
assg2 = DifferentialAssignment(
    foxes, 0.1 * sym.sympify("foxes") * sym.sympify("rabbits")
)
predation = VariablePortedObject("predation", [assg1, assg2])

cpo_eco = CompositePortedObject("ecosystem")
cpo_eco.add_child(rabbit_growth)
cpo_eco.add_child(fox_growth)
cpo_eco.add_child(predation)
cpo_eco.add_variable_port(VariablePort("foxes"))
cpo_eco.add_variable_port(VariablePort("rabbits"))
cpo_eco.add_variable_aggregation_wiring(
    ["rabbit growth.rabbits", "predation.rabbits"], "rabbits"
)
cpo_eco.add_variable_aggregation_wiring(
    ["fox growth.foxes", "predation.foxes"], "foxes"
)

compiled = cpo_eco.compile()

for s in compiled.symbol_identifications:
    print(s)
for sc in compiled.get_all_symbol_containers():
    print(sc)

var, par = compiled.get_assignments()
sys = System(variable_assignments=var, parameter_assignments=par)

for var in sys.variables:
    print(f"d({var.symbol})/dT = {var.update_rule.equation}")

sys.simulate(
    t_end=50, n_steps=24, mode="cts"
)  # Simulate for 100 days, 24 steps per day (hourly simulation)

sys.plot_solution({"rabbits", "foxes"})

for var in sys.variables:
    print(f"d({var.symbol})/dT = {var.update_rule.equation}")

print("Final values:")
for symbol, value in zip(sys.variables.get_symbols(), sys.variables.get_final_values()):
    print(f"{symbol} = {value}")
