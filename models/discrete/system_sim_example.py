from populations import *

A = Population("A", initial_value=100)
B = Population("B", initial_value=1)

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
print([v.symbol for v in AB.update_rules[0].all_variables])

print("Uncombined update rules:", [str(u) for u in AB.update_rules])

system = AB.compile()

print("Combined update rules:", [str(u) for u in system.update_rules])

'''
We have created the system
    d[x_A]/dt = 30 - 0.9*x_A
    d[x_B]/dt = x_A - 1.1*x_B
which has a stable fixed point (x_A, x_B) = (100/3, 1000/33) ~ (33.3333, 30.3030)
'''
system.simulate(t_end=100, n_steps=24)  # Simulate for 100 days, 24 steps per day (hourly simulation)

print(system.variables.get_symbols(), system.variables.get_final_values())







