### Simple predator-prey model

from ODEBuilder import *

rats = Unit('rats',50)
cats = Unit('cats',20)

rats.add_growth_rate(3)
cats.add_growth_rate(-0.8)

Sys = System('Rats and Cats')

Sys.add_system(rats)
Sys.add_system(cats)

Sys.add_interaction(rats,cats,-0.1,0.03)

print(Sys.get_ODEs_subbed()) ### prints system ODEs with parameters

Sys.sol([0,25],print=True)


