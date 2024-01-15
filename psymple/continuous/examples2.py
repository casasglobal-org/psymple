### Single species logistic model with time-dependent growth rate

import sympy as sym
from system import System
from equation import Unit

beetles = Unit('beetles', 500, growth_rate=2*sym.sin(System.T)+0.3, capacity=20000)

Sys = System('beetles')
Sys.add_equation(beetles)

sol = Sys.solve([0,25])
sol.plot()

