### Two-species interaction between worms and birds, with birds having subunits eggs and adults. 
### Work in progress! Parameters need tuning.

from ODEBuilder import *

### Define the 3 species: Worms, Bird Eggs, Bird Adults, and initial rates

Worms = Unit('Worms',100)

BirdEggs = Unit('BirdEggs',50)
BirdAdults = Unit('BirdAdults',0)

Worms.add_growth_rate(1)
BirdEggs.add_growth_rate(-1)
BirdEggs.add_capacity(1000)

### Group the Bird Eggs and Bird Adults into a Birds population, and link eggs to adults

Birds = Population('Birds')

Birds.add_unit(BirdEggs)
Birds.add_unit(BirdAdults)

Birds.link_lifestage(BirdEggs,BirdAdults,1)

### Add everything into a System, and add predator-prey interations between worms and birds

ODE = System()

ODE.add_system(Worms)
ODE.add_system(Birds)

ODE.add_interaction(Worms,BirdEggs,0,0.02)
ODE.add_interaction(Worms,BirdAdults,-0.5,0)

print(ODE.get_ODEs_subbed()) ### prints system ODEs with parameters

### Solve and print the system

ODE.sol([0,25],print = True)

