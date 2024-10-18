import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    System,
)

"""
Recall the following variable object 'pop' capturing Malthusian growth in a reusable way.
"""

pop = VariablePortedObject(
    name="malthusian_pop",
    assignments=[("x", "r*x")],
    input_ports=[("r", 0.1)],
)

"""
Logistic population growth consists of a Malthusian growth component and a density-dependent limit to some
carrying capacity K. The differential equation is dx/dt = rx(1 - x/K). 

We could create a new variable object capturing this equation, but since we have already have the object
'pop' capturing Malthusian growth, it feels as though we are repeating some work. 

Here is an alternative way of viewing the logistic growth equation: its right-hand side is the sum of 
two components: a Malthusian component rx, and a limit component -x^2/K. Psymple allows us to combine
two variable objects, each capturing one of these components, to a single dynamic model in a process
called composition. 

In simple terms, the composition of the equations dx/dt = f(x,t) and dx/dt = g(x,t) is the equation
dx/dt = f(x,t) + g(x,t). Let's see how to do this in psymple. First we need a variable object 
capturing the logistic component, with a default value of 'K = 10'.
"""

limit = VariablePortedObject(
    name="logistic_limit",
    assignments=[("x", "- r* x**2 / K")],
    input_ports=[("r", 0.1), ("K", 10)],
)

"""
Next, in a composite object, we use a variable wire to tell psymple to compose the variables
'malthusian_pop.x' and 'logistic_limit.x' together. To do this, we specify a wire
`wire = {"child_ports": ["malthusian_pop.x", "logistic_limit.x"], "output_name" = "x"}`. There is
a shorthand for this, which at first appears unnatural:
`wire = (["malthusian_pop.x", "logistic_limit.x"], None, "x")`. We will discuss this shortly.
"""

logistic_pop = CompositePortedObject(
    name="logistic_pop",
    children=[pop, limit],
    variable_wires=[(["malthusian_pop.x", "logistic_limit.x"], None, "x")],
)

system = System(logistic_pop)
system.compile()

sim = system.create_simulation("sim", solver="discrete", initial_values={"x": 1})
sim.simulate(100, n_steps=10)
sim.plot_solution()

"""
You'll that the simulation looks exactly as expected: the population initially undergoes exponential
growth, before its growth rate slows and it approaches the limit of 10. 

Let's discuss some efficiencies and good practice. Suppose instead that we did implement the logistic
growth equation as a single variable object:

logistic_pop = VariablePortedObject(
    name="logistic_pop",
    assignments=[("x", "r*(x - x**2/K)")],
    input_ports=[("r", 0.1), ("K", 10)],
)

As discussed, this implementation does not exploit the reusability features of psymple, but there are three
apparent advantages:
    (1) The default value for "r" only had to be specified once.
    (2) The variable "x" is available for composition in larger systems.
    (3) The object as a whole has a clean form: it is an object depending on input parameters "r" and "K",
        and makes the variable "x" available to the wider system.

Fortunately, composite objects in psymple allow for all of these to be implemented, and this is how
psymple is intended to be used in best practice to allow for full modularity and reusablity. To achieve this,
composite objects can be given their own ports: input ports to read parameters or specify default values, and
variable ports to expose variables and their differential equations for composition. These ports connect to 
wires in the ways we've already seen.

With this in mind, let's see how we would build up the logistic_pop object to both maximise modularity and
reusability. We first take the two variable components 'pop' and 'limit'.
"""

pop = VariablePortedObject(
    name="malthusian_pop",
    assignments=[("x", "r*x")],
)

limit = VariablePortedObject(
    name="logistic_limit",
    assignments=[("x", "- r* x**2 / K")],
)

"""
Notice that we have not specified default input ports. Psymple is able to automatically generate the port 
'r' in 'pop' and the ports 'r' and 'K' in 'limit'. Given we know that we will specify these later, we don't 
need to give default values at this stage.

Next, we will define the composite object 'logistic_pop' 
"""

logistic_pop = CompositePortedObject(
    name="logistic_pop",
    children=[pop, limit],
    input_ports = [("r", 0.1), ("K", 10)],
    variable_ports=["x"],
    variable_wires=[(["malthusian_pop.x", "logistic_limit.x"], "x")],
    directed_wires=[
        ("r", ["malthusian_pop.r", "logistic_limit.r"]),
        ("K", "logistic_limit.K"),
    ],
)

"""
There's a bit to look at here. First, notice that we have given input ports to 'logistic_pop' in
the same way we did for our previous variable objects. We have also told psymple to form a
variable port 'x' on 'logistic_pop', so that we can expose internal information.

Next, notice that the variable wire has nearly the same format - but this time the given format
is shorthand for `wire = {"child_ports": ["malthusian_pop.x", "logistic_limit.x"], "parent_port": "x"}`.
So instead of just assigning the name of the composition of these variables to 'x', we're now saying to
expose that composition at variable port 'x'.

Finally, we've used two directed wires to connect our ports and objects. The first wire,
`("r", ["malthusian_pop.r", "logistic_limit.r"])` transfers the default value at port 'r' to *both*
'malthusian_pop.r' and 'logistic_limit.r'. The second wire transfers the default value of 'K' to
'logistic_limit.K'. 

Let's finish by checking that this new, general object does the same thing as before.
"""

system = System(logistic_pop)
system.compile()

sim = system.create_simulation("sim", solver="discrete", initial_values={"x": 1})
sim.simulate(100, n_steps=10)
sim.plot_solution()

