### Simple predator-prey model

from system import Population
from equation import Unit

rats = Unit('rats', 50, growth_rate=3)
cats = Unit('cats', 20, growth_rate=-0.8)

Sys = Population('Rats and Cats')

Sys.add_equation(rats)
Sys.add_equation(cats)

Sys.add_interaction(rats, cats, -0.1, 0.03)
sol = Sys.solve([0,25])
sol.plot()


