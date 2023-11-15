from populations import *
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


A = Population("A")
B = Population("B")

A._add_parameter("basic", "growth_A", "r", 0.1)
B._add_parameter("basic", "growth_B", "r", -0.1)
A._add_update_rule('x_A', 'r_growth_A * x_A')
B._add_update_rule('x_B', 'r_growth_B * x_B')

AB = Population("AB")

AB._add_population(A)
AB._add_population(B)

AB._add_parameter("basic", "flow_AB", "f", 1)
AB._add_parameter("basic", "control_A", "c", 30)

AB._add_update_rule('x_A', '-f_flow_AB * x_A + c_control_A')
AB._add_update_rule('x_B', 'f_flow_AB * (x_A - x_B)')

AB.variables[1].initial_value = 100  # Need initial value setting
AB.variables[2].initial_value = 1

AB.variables._edit("remove", 0)

sys = AB.compile()

print([(var.symbol, var.equation.equation, var.equation.equation_subbed) for var in sys.variables])

"""
We have created the system
    d[x_A]/dt = 30 - 0.9*x_A
    d[x_B]/dt = x_A - 1.1*x_B
which has a stable fixed point (x_A, x_B) = (100/3, 1000/33) ~ (33.3333, 30.3030)
"""

sys.simulate(t_end=10, n_steps=24)  # Simulate for 100 days, 24 steps per day (hourly simulation)
"""
plt.plot(sys.system_time.time_series, sys.variables[0].time_series)
plt.plot(sys.system_time.time_series, sys.variables[1].time_series)
plt.grid()
plt.show()

"""





print(sys.variables.get_symbols(), sys.variables.get_final_values())
