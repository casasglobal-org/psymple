### Simple predator-prey model

from ODEBuilder import *

rats = Population('rats')
cats = Population('cats')

rats.add_growth_rate(3)
cats.add_growth_rate(-0.8)

ODE = System()

ODE.add_population(rats)
ODE.add_population(cats)

ODE.add_interaction(rats,cats,-0.1,0.03)

print(ODE.get_ODEs_subbed()) ### prints system ODEs with parameters

sol = ODE.sol([0,25],[50,20]) ### solves system for time range (0,25), initial values rats = 50, cats = 20

print_sol(sol,[0,25])


