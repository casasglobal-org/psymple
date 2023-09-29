### Single species logistic model with time-dependent growth rate

from ODEBuilder import *

beetles = Population('beetles')

beetles.add_growth_rate(2*sym.sin(T)+0.3)
beetles.add_capacity(60000)

ODE = System()

ODE.add_population(beetles)

print(ODE.get_ODEs_subbed()) ### prints system ODEs with parameters

sol = ODE.sol([0,25],[5000])
print_sol(sol,[0,25])