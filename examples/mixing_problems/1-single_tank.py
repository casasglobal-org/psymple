import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    CompositePortedObject,
    VariablePortedObject,
    System,
)

"""
In these examples we will consider how to model _mixing problems_ in `psymple`. A mixing problem
seeks to understand the evolution of a quantity of solvent in a solute, for example a chemical
being mixed in a tank of water. These problems can be highly varied, for example solution can
enter a tank at variable concentration or rate, or leave the tank at variable rate. Alternatively,
several tanks can be connected together, with their solutions being pumped into each other.

We will assume that tanks are _well-mixed_, that is, the concentration of the solute is the same
throughout the tank at any moment in time. 

First, we will consider a single tank with an initial volume of water \( V_0 l \) and an initial
amount of \( M_0 g \) of salt dissolved in it. A solution with concentration \( c(t) g/l \) of
salt flows into the tank at rate \( r_0(t) l/s \) and the mixed solution flows out of the tank at
a rate of \( r_1(t) l/s \).

Let \( V(t) \) be the volume of solution in the tank at time \( t \). Then 
\( V'(t) = r_0(t) - r_1(t) \). Furthermore, let \( M(t) \) be the amount of salt in the solution
at time \( t \). The rate of change of salt in the solution is given by
\( M'(t) = r_0(t) c(t) - r_1(t) M(t)/V(t) \).

In `psymple`, we could model \( V(t) \) and \( M(t) \) by writing just writing the two differential
equations above. In that case, however, our model would become fixed, and if we considered a new
situation with more than one in-flow or out-flow, we would have to build something new. Instead,
consider what is happening at each point a pipe meets the tank. For the in-flow pipe, there are
fluxes \( V'(t) = r_0(t) \) and \( M'(t) = r_0 (t) c(t) \). For the out-flow pipe, we similarly
get \( V'(t) = -r_1(t) \) and \( M'(t) = - r_1(t) M(t)/V(t) \). The situation inside the tank
is then nothing but the aggregation of these volume and mass variables.

We model this initially with two `VariablePortedObject` instances, as follows.
"""

pipe_in = VariablePortedObject(
    name="pipe_in",
    assignments=[
        ("V", "r_0"),
        ("M", "r_0*c"),
    ],
)

pipe_out = VariablePortedObject(
    name="pipe_out",
    assignments=[
        ("V", "-r_1"),
        ("M", "-r_1 * M/V"),
    ]
)

"""
Using a `CompositePortedObject`, we can then aggregate the variables of these two objects together,
and expose the parameters `r_0`, `r_1` and `c`.
"""

tank = CompositePortedObject(
    name="tank",
    children=[pipe_in, pipe_out],
    input_ports=["r_0", "r_1", "c"],
    variable_ports=["V", "M"],
    variable_wires=[
        (["pipe_in.V", "pipe_out.V"], "V"),
        (["pipe_in.M", "pipe_out.M"], "M"),
    ],
    directed_wires=[
        ("r_0", "pipe_in.r_0"),
        ("r_1", "pipe_out.r_1"),
        ("c", "pipe_in.c")
    ]
)

"""
That's it! Let's define and compile a `System` class for `tank`.
"""

system = System(tank)
system.compile()

print(system)

"""
Before we can simulate, we need to provide values for the flow rates and concentration in. We can 
we can do this when we create a simulation, allowing us to experiment with multiple scenarios. 

We'll try the following. For each, we'll set initial values of \( V_0 = 1000l \) and \( M_0 = 20g \).

1. \( r_0 = 4 = r_1 \) and \( c = 0.5 \). In this case, the volume of the tank should stay constant,
    and the amount of salt should continually increase towards a limit.
2. \( r_0 = 2 \), \( r_1 = 4 \) and \( c = 0.5 \). In this case, the volume of the tank will decrease.
3. Being more creative, we can set \( r_0 = 4sin(t) + 4 \) and \( r_1 = 4 \), \( c = 0.5 \). The
    volume of the tank will fluctuate, but stay centred around 1000l. 
4. Instead, \( r_0 = 4 = r_1 \) and \( c = 0.5sin(t) + 0.5 \). 
"""

for name, inputs in zip(
    ["sim_1", "sim_2", "sim_3", "sim_4"],
    [
        {"r_0": 4, "r_1": 4, "c": 0.5},
        {"r_0": 2, "r_1": 4, "c": 0.5},
        {"r_0": "4*sin(T) + 4", "r_1": 4, "c": 0.5},
        {"r_0": 4, "r_1": 4, "c": "0.5*sin(T) + 0.5"},
    ]
):
    sim = system.create_simulation(name, solver="discrete", initial_values={"V": 1000, "M": 20}, input_parameters=inputs)
    sim.simulate(10, n_steps=1)

system.simulations["sim_1"].plot_solution({"M"})
system.simulations["sim_1"].plot_solution({"V"})