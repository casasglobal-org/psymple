from DiscretisedModel_v2 import *
import matplotlib.pyplot as plt

FlyEggs = Age_Structured_Population("fly_eggs", "DDTM", [10, 47.2, 9.1, DegreeDays, False, False])

FlyEggs.set_initial_value(FlyEggs.first, 100)

print([v.values_vector[-1] for v in FlyEggs.variables]) ### Initial values

FlyEggs.expressions.reverse() ### Runs the updates from last to first: need to include in core functionality

Sys = System("Flies", FlyEggs, FlyEggs.expressions)

print([FlyEggs.expressions[i].equation for i in range(len(FlyEggs.expressions))])

print([v.symbol for v in FlyEggs.variables])



Sys.update(10)      ### Update the DDTM for 1 day with 10 sub-steps per day. 
                    ### Call Sys.update(10) multiple times for multiple days.

print(f"day 1 values: {[v.values_vector[-1] for v in FlyEggs.variables]}")

n_days = 9

for i in range(n_days):
    Sys.update(10)
    print(f"day {i+2} values: {[v.values_vector[-1] for v in FlyEggs.variables]}")


'''
TODO: Need to only print every other value (bug)
t = np.linspace(0,10,201)
plt.plot(t, np.transpose([FlyEggs.variables[i].values_vector for i in range(1,len(FlyEggs.variables)-1)]))
#plt.legend([self.components[i].name for i in range(len(self.components))], loc='best')
plt.xlabel('t')
plt.grid()
plt.show()
'''

