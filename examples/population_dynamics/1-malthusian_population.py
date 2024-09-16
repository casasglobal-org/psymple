import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
)
from psymple.build import System

"""
The most basic population dynamics model is \( dx/dt = rx \).

This equation can be formed as a VariablePortedObject with an assignment 
`assg = {"variable": "x", "expression": "r*x"}`. This entry is equivalent to the shorthand
`assg = ("x", "r*x")`.

The value of parameter 'r' could be specified immediately in the assignment, for example we
could instead write the assignment ("x", "0.1*x"). 

Alternatively, psymple allows you to specify a value for 'r' through an input port. This
has two advantages:
    (1) the variable ported object becomes a general, reusable object
    (2) the default value can be overwritten from elsewhere in a larger system

We will see an example of (2) shortly. For now, to a default value of 0.1 for the parameter
'r', we add an input port `port = {"name": "r", "default_value": 0.1}`. As for assignments,
this is equivalent to the shorthand `port = ("r", 0.1)`.

Putting these together, we define the VariablePortedObject `pop` as follows.
"""

pop = VariablePortedObject(
    name="malthusian_pop",
    assignments=[("x", "r*x")],
    input_ports=[("r", 0.1)],
)

"""
The following commands create, run and plot a simulation of our equation with initial condition
'x = 1'. 
"""

system_1 = System(pop)
system_1.compile()

sim_1 = system_1.create_simulation("sim", solver="discrete", initial_values={"x": 1})
sim_1.simulate(10, n_steps=10)
sim_1.plot_solution()

"""
Now let's see an example of overriding a default parameter value. Suppose that we individually know
the birth rate 'b' and death rate 'd' for the population, with values 0.4 and 0.2, respectively. 
The combined Malthusian rate is 'r = b - d'. We can perform this calculation in a FunctionalPortedObject
with assignment `assg = {"parameter": "r", "expression": "b-d"}`. As before, this is equivalent to the
shorthand `assg = ("r", "b-d")`.

Again, we need to tell psymple what we mean by 'b' and 'd', which we can do as default input ports on
this object.
"""

rate = FunctionalPortedObject(
    name="rate",
    assignments=[("r", "b-d")],
    input_ports=[("b", 0.4), ("d", 0.2)],
)

"""
Next, we need to tell our variable object 'pop' to read its value of 'r' from the value of 'r' produced
by the function 'rate'. We do this in a CompositePortedObject containing both 'pop' and 'rate' as 
children, using a directed wire from 'rate.r' to 'malthusian_pop.r'. This is written as 
`wire = {"source": "rate.r", "destination": "malthusian_pop.r"}`. There is, of course, an equivalent 
shorthand `wire = ("rate.r", "malthusian_pop.r")`. 
"""

pop_system = CompositePortedObject(
    name="malthusian_pop_system",
    children=[pop, rate],
    directed_wires=[("rate.r", "malthusian_pop.r")],
)

"""
Notice that we did not have to redefine the variable object 'pop'. Since we defined it generally,
we can reuse its mechanics over and over again. The following commands simulate and plot this
new system.
"""

system_2 = System(pop_system)
system_2.compile()

sim_2 = system_2.create_simulation("sim", solver="discrete", initial_values={"malthusian_pop.x": 1})
sim_2.simulate(10, n_steps=10)
sim_2.plot_solution()