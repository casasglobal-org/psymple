from populations import *

A = Population("A")
B = Population("B")

A._add_parameter("basic", "growth_A", "r", 0.1)
B._add_parameter("basic", "growth_B", "r", -0.1)

A._add_update_rule('x_A', '0.1 * x_A')
# should be A._add_update_rule('x_A', 'r_growth_A * x_A')
B._add_update_rule('x_B', '-0.1 * x_B')
# B._add_update_rule('x_B', 'r_growth_B * x_B')

AB = Population("AB")

AB._add_population(A)
AB._add_population(B)

AB._add_parameter("basic", "flow_AB", "f", 1)
AB._add_parameter("basic", "control_A", "c", 30)

AB._add_update_rule('x_A', '-x_A + 30')
# AB._add_update_rule('x_A', 'flow_AB * x_A + c_control_A')
AB._add_update_rule('x_B', '(x_A - x_B)')
# AB._add_update_rule('x_B, 'flow_AB * (x_A - x_B)')

AB.variables[1].time_series = [100] # Need initial value setting
AB.variables[2].time_series = [1]

print("Uncombined update rules:", [str(u) for u in AB.update_rules])

sys = AB.compile()

print("Combined update rules:", [str(u) for u in sys.update_rules])

'''
We have created the system
    d[x_A]/dt = 30 - 0.9*x_A
    d[x_B]/dt = x_A - 1.1*x_B
which has a stable fixed point (x_A, x_B) = (100/3, 1000/33) ~ (33.3333, 30.3030)
'''
sys.simulate(t_end = 100, n_steps = 24)   #Simulate for 100 days, 24 steps per day (hourly simulation)

print(sys.variables.get_symbols(), sys.variables.get_final_values())







