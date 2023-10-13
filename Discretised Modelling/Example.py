from DiscretisedModel_v2 import *

FlyEggs = DDTM("fly eggs", 10, 27.2, 8)

FlyEggs.first().set_initial_value(400)

print([v.values_vector[-1] for v in FlyEggs.variables]) ### Initial values

FlyEggs.expressions.reverse() ### Runs the updates from last to first: need to include in core functionality

Sys = System("Flies", FlyEggs, FlyEggs.expressions)

Sys.update(10)      ### Update the DDTM for 1 day with 10 sub-steps per day. 
                    ### Call Sys.update(10) multiple times for multiple days (uncomment below). Model dies out in about 7 days

print(f"day 1 values: {[v.values_vector[-1] for v in FlyEggs.variables]}")


n_days = 10

for i in range(n_days):
    Sys.update(10)
    print(f"day {i+2} values: {[v.values_vector[-1] for v in FlyEggs.variables]}")


