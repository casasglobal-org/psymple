# Mixing problems

In these examples we will consider how to model _mixing problems_ in `psymple`. A mixing problem seeks to understand the evolution of a quantity of solvent in a solute, for example a chemical being mixed in a tank of water. These problems can be highly varied, for example solution can enter a tank at variable concentration or rate, or leave the tank at variable rate. Alternatively, several tanks can be connected together, with their solutions being pumped into each other.

## Assumptions

We will assume that tanks are _well-mixed_, that is, the concentration of the solute is the same throughout the tank at any moment in time.

## Single tank

First, we will consider a single tank with an initial volume of water $V_0\,\mathrm{l}$ and an initial amount of $M_0\,\mathrm{g}$ of salt dissolved in it. A solution with concentration $c(t)\,\mathrm{g}/\mathrm{l}$ of salt flows into the tank at rate $r_0(t)\,\mathrm{l}/\mathrm{s}$ and the mixed solution flows out of the tank at a rate of $r_1(t)\,\mathrm{l}/\mathrm{s}$.

Let $V(t)$ be the volume of solution in the tank at time $t$. Then  $V'(t) = r_0(t) - r_1(t)$. Furthermore, let $M(t)$ be the amount of salt in the solution at time $t$. The rate of change of salt in the solution is given by $M'(t) = r_0(t) c(t) - r_1(t) M(t)/V(t)$.

### Modelling flows in `psymple`

In `psymple`, we could model $V(t)$ and $M(t)$ by writing just writing the two differential equations above. In that case, however, our model would become fixed, and if we considered a new situation with more than one in-flow or out-flow, we would have to build something new. Instead, consider what is happening at each point a pipe meets the tank. 

For the in-flow pipe, there are fluxes $V'(t) = r_0(t)$ and $M'(t) = r_0 (t) c(t)$. For the out-flow pipe, we similarly get $V'(t) = -r_1(t)$ and $M'(t) = - r_1(t) M(t)/V(t)$. The situation inside the tank is then nothing but the aggregation of these volume and mass variables.

We model this initially with two `VariablePortedObject` instances. 

```py
from psymple.build import VariablePortedObject
```

First, the model for the in pipe is:

``` py title="tank in-flow model"
pipe_in = VariablePortedObject(
    name="pipe_in",
    assignments=[
        ("V", "r_0"),
        ("M", "r_0*c"),
    ],
)
```

and the model for the out pipe is:

```py title="tank out-flow model"
pipe_out = VariablePortedObject(
    name="pipe_out",
    assignments=[
        ("V", "-r_1"),
        ("M", "-r_1 * M/V"),
    ]
)
```

### Defining the system model

Using a `CompositePortedObject`, we can then aggregate the variables of these two objects together, and expose the parameters `r_0`, `r_1` and `c`.

```py title="single tank model"
from psymple.build import CompositePortedObject

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
```

That's it! Let's define and compile a `System` class for `tank`.

### Simulating the model

```py title="tank system"
from psymple.build import System

system = System(tank) # (1)!
system.compile()
```

1. It is also possible to call `System(tank, compile=True)`. In this case, the command `system.compile()` doesn't need to be called.

Before we can simulate, we need to provide:

- Initial values for the variables mass `"V"` and salt amount `"M"`. These are provided using a dictionary passed to the argument `initial_values` when a simulation is created. 
- Values for the flow rates and concentration in. We can either do this using the method `system.set_parameters`, or as we do here, by passing a dictionary to the argument `input_parameters` when creating a simulation, allowing us to experiment with multiple scenarios. 

We will construct four simulations. For each, we'll set initial values of $V_0 = 1000$ and $M_0 = 20$. The input parameters for each simulation will be:

1. $r_0 = 4 = r_1$ and $c = 0.5$. In this case, the volume of the tank should stay constant,
    and the amount of salt should continually increase towards a limit.
2. $r_0 = 2$, $r_1 = 4$ and $c = 0.5$. In this case, the volume of the tank will decrease.
3. Being more creative, we can set $r_0 = 4sin(t) + 4$ and $r_1 = 4$, $c = 0.5$. The
    volume of the tank will fluctuate, but stay centred around $1000$.
4. Instead, $r_0 = 4 = r_1$ and $c = 0.5sin(t) + 0.5$. 

```py title="Setting up the simulations"
for name, inputs in zip(
    ["sim_1", "sim_2", "sim_3", "sim_4"], # (1)!
    [
        {"r_0": 4, "r_1": 4, "c": 0.5}, # (2)!
        {"r_0": 2, "r_1": 4, "c": 0.5},
        {"r_0": "4*sin(T) + 4", "r_1": 4, "c": 0.5},
        {"r_0": 4, "r_1": 4, "c": "0.5*sin(T) + 0.5"},
    ]
):
    sim = system.create_simulation(
        name=name, 
        solver="discrete", 
        initial_values={"V": 1000, "M": 20}, # (3)!
        input_parameters=inputs,
    )
    sim.simulate(10, n_steps=1000)
```

1. These are the names for each simulation.
2. For each simulation, the set of input parameters is passed as a dictionary.
3. The initial values for each simulation are defined here. They can also be varied in the same way as the input parameters are varied.

Finally, we can visualise each model run by using the `plot_solution` method. Each simulation can be accessed from the dictionary `system.simulations` using the keys `"sim_1"`, `"sim_2"`, `"sim_3"` or `"sim_4"`.

```py title="plotting solutions"
system.simulations["sim_1"].plot_solution({"M"})
system.simulations["sim_1"].plot_solution({"V"})
```