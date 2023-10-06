### Single species logistic model with time-dependent growth rate

from ODEBuilder import *

beetles = Unit('beetles',500)

beetles.add_growth_rate(2*sym.sin(T)+0.3)
beetles.add_capacity(20000)

print(beetles.get_ODEs_subbed()) ### prints system ODEs with parameters

beetles.sol([0,25],print = True)