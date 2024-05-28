import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

# import matplotlib.pyplot as plt
from psymple.populations import Population
from psymple.system import System

A = Population("A", initial_value=100)
B = Population("B", initial_value=1)

A._add_parameter("basic", "growth_A", "r", 0.1)
B._add_parameter("basic", "growth_B", "r", "-0.1")
A._add_update_rule("x_A", "r_growth_A * x_A")
B._add_update_rule("x_B", "r_growth_B * x_B")

AB = Population("AB")

AB._add_population(A)
AB._add_population(B)

AB._add_parameter("basic", "flow_AB", "f", 1)
AB._add_parameter("basic", "control_A", "c", 30)

AB._add_update_rule("x_A", "-f_flow_AB * x_A + c_control_A")
AB._add_update_rule("x_B", "f_flow_AB * (x_A - x_B)")

sys = System(AB)

for var in sys.variables:
    print(f"d({var.symbol})/dT = {var.update_rule.equation}")

"""
We have created the system
    d[x_A]/dt = 30 - 0.9*x_A
    d[x_B]/dt = x_A - 1.1*x_B
which has a stable fixed point (x_A, x_B) = (100/3, 1000/33) ~ (33.3333, 30.3030)
"""

sys.simulate(
    t_end=100, n_steps=24, mode="cts"
)  # Simulate for 100 days, 24 steps per day (hourly simulation)

sys.plot_solution({"x_A", "x_B"}, (0, 10))

sys.plot_solution({
    "x_A" : "r+",
    "x_B" : {
        "color": 'green',
        "marker": 'o',
        "linestyle": 'dashed',
        "linewidth": 2,
    }
})

for var in sys.variables:
    print(f"d({var.symbol})/dT = {var.update_rule.equation}")

print("Final values:")
for symbol, value in zip(sys.variables.get_symbols(), sys.variables.get_final_values()):
    print(f"{symbol} = {value}")
