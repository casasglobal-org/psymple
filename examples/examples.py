import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from psymple.populations import IndexedPopulation, Population
from psymple.variables import Parameter

FlyEggs1 = Population("flyeggs1")
FlyEggs2 = Population("flyeggs2")

FlyEggs = IndexedPopulation("flyeggs", (2,))

FlyEggs.add_population(FlyEggs1, 0)
FlyEggs.add_population(FlyEggs2, 1)

print(FlyEggs[1].variables.get_symbols())


FlyLarvae = Population("flylarvae")

Flies = Population("flies")

Flies._add_population(FlyEggs)
Flies._add_population(FlyLarvae)

print(Flies.variables.get_symbols())

Flies._add_parameter("basic", "growth_rate", "r", 45)

Flies._add_update_rule(FlyEggs1.variable, "r_growth_rate * x_flyeggs1")

Flies._add_update_rule(
    "x_flyeggs1", Flies.parameters.growth_rate.symbol * FlyEggs1.variable.symbol
)

P = Parameter.basic("P", "param", "p")
Q = Parameter.basic("Q", "param", "q")
R = Parameter.basic("R", "param", "r")

X = Parameter.composite("X", "comp", P.symbol + Q.symbol**2)

Y = Parameter.composite("Y", "comp", X.symbol * R.symbol)

Z = Parameter.composite("Z", "comp", "exp(param_P * comp_X + comp_Y)")

print(str(Z))
