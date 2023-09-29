### Two-species interaction between worms and birds, with birds having subunits eggs and adults. 
### Work in progress! Parameters need tuning.

from ODEBuilder import *

worms = Population('worms')
birds = Population('birds')

eggs = Subpopulation('eggs',birds)
adults = Subpopulation('adults',birds)

worms.add_growth_rate(3)
eggs.add_growth_rate(-1)
eggs.add_capacity(1000)
adults.add_growth_rate(-0.5)
birds.link_lifestage(adults,eggs,1)

ODE = System()

ODE.add_population(worms)
ODE.add_population(birds)

ODE.add_interaction(worms,eggs,0,1/45)
ODE.add_interaction(worms,adults,-0.1,0)

print(ODE.get_ODEs_subbed()) ### prints system ODEs with parameters

sol = ODE.sol([0,10],[50,45,0])

print_sol(sol,[0,10])

