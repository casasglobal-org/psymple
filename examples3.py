### Two-species interaction between worms and birds, with birds having subunits eggs and adults. 
### Work in progress! Parameters need tuning.

from system import Population, System
from equation import Unit

### Define the 3 species: Worms, Bird Eggs, Bird Adults, and initial rates

Worms = Unit('Worms', 100, growth_rate=1)

BirdEggs = Unit('BirdEggs', 50, growth_rate=-1, capacity=1000)
BirdAdults = Unit('BirdAdults', 0)

### Group the Bird Eggs and Bird Adults into a Birds population, and link eggs to adults

Birds = Population('Birds')

Birds.add_equation(BirdEggs)
Birds.add_equation(BirdAdults)

Birds.link_lifestage(BirdEggs, BirdAdults, 1)

### Add everything into a System, and add predator-prey interations between worms and birds

ODE = Population("Ecosystem")

ODE.add_system(Birds)
ODE.add_equation(Worms)

ODE.add_interaction(Worms, BirdEggs, 0, 0.02)
ODE.add_interaction(Worms, BirdAdults, -0.5, 0)

# print(ODE.get_ODEs_subbed()) ### prints system ODEs with parameters

### Solve and print the system

sol = ODE.solve([0,25])
sol.plot()
