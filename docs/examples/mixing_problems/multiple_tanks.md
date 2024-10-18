In the previous example, we considered a mixing problem with a single tank, which had an external flow in and an external flow out. Now we consider a mixing problem consisting of two or more tanks, each of which can have external flows in and out in the same manner as for the single tank, and which furthermore can have flows to and from other tanks in the system.

It will help to first specify the system data. In this case, we will create a system with \( n > 1 \) tanks, such that every tank has a flow in and flow out, plus a flow to and from every other tank. The following data can be freely altered to reduce the external flows and connections, if desired.

```py title="system data"
# Number of tanks
n = 2

# List of tanks created
tanks_id = [i for i in range(1, n + 1)]

# List of pipes between tanks eg. (1,2) is a pipe from tank 1 to tank 2
link_pipes_id = [
    (i, j) 
    for i in tanks_id 
    for j in tanks_id 
    if j != i
]

# List of tanks with an external pipe in
pipes_in_id = [1, 2]

# List of tanks with an external pipe out
pipes_out_id = [1, 2]
```

If you followed through the single tank example, the following lists of pipes in and out are created in exactly the same way as there. We create pipes in for every tank in `pipes_in_id` and pipes out for every tank in `pipes_out_id`.

```py
from psymple.build import VariablePortedObject

pipes_in = [
    VariablePortedObject(
        name=f"in_{i}",
        assignments=[
            ("Q_in", "rate * conc"),
            ("V_in", "rate"),
        ],
    )
    for i in pipes_in_id
]

pipes_out = [
    VariablePortedObject(
        name=f"out_{i}",
        assignments=[
            ("Q_out", "-rate * Q_out / V_out"), 
            ("V_out", "-rate")
        ],
    )
    for i in pipes_out_id
]
```

Next, we need to define connector pipes. These have four variables:

- `Q_in`, the amount of salt entering the pipe from a tank,
- `Q_out`, the amount of salt flowing into the next tank. Note that this has the same concentration
    as for `Q_in`,
- `V_in`, the volume of water entering the pipe from the tank,
- `V_out`, the volume of water exiting the pipe into the next tank.

We create a connector pipe for every pair in `link_pipes_id`.

```py
connectors = [
    VariablePortedObject(
        name=f"pipe_{i}_{j}",
        assignments=[
            ("Q_in", "- rate * Q_in / V_in"),
            ("Q_out", "rate * Q_in / V_in"),
            ("V_in", "-rate"),
            ("V_out", "rate"),
        ],
    )
    for i, j in link_pipes_id
]
```

Now we just need to define our system of tanks. Compared to the single tank example, the children, variable ports and input ports are exactly the same (just one for each tank, if it was specified), except for additionally the specification of the flow rates `rate_i_j` of the connector pipes as additional input ports.

The directed wires simply connect the rates at the input ports to the correct pipes.

The only thing which becomes more complicated is the aggregation of the variables. Each tank `i`, and therefore each variable `Q_i` (and `V_i`), can have:

- External in-flows if `i in pipes_in_id`,
- External out-flows if `i in pipes_out_id`,
- A flow to tank `j` for every `j` such that `(i,j) in link_pipes_id`,
- A flow from tank `j` for every `j` such that `(j,i) in link_pipes_id`.

The variable_wires data simply aggregates all these variables to `Q_i` (and `V_i`).

```py title="tanks model"
from psymple.build import CompositePortedObject

tanks = CompositePortedObject(
    name="tanks",
    children=pipes_in + pipes_out + connectors,
    variable_ports=[f"Q_{i}" for i in tanks_id]
    + [f"V_{i}" for i in tanks_id],
    input_ports=[f"rate_{i}_{j}" for i, j in link_pipes_id]
    + [f"conc_in_{i}" for i in pipes_in_id]
    + [f"rate_in_{i}" for i in pipes_in_id]
    + [f"rate_out_{i}" for i in pipes_out_id],
    directed_wires=[
        (f"rate_{i}_{j}", f"pipe_{i}_{j}.rate")
        for i, j in link_pipes_id
    ]
    + [(f"conc_in_{i}", f"in_{i}.conc") for i in pipes_in_id]
    + [(f"rate_out_{i}", f"out_{i}.rate") for i in pipes_out_id]
    + [(f"rate_in_{i}", f"in_{i}.rate") for i in pipes_in_id],
    variable_wires=[
        (
            ([f"in_{i}.Q_in"] if i in pipes_in_id else [])
            + ([f"out_{i}.Q_out"] if i in pipes_out_id else [])            
            + [f"pipe_{j}_{i}.Q_out" for j in tanks_id if j != i]
            + [f"pipe_{i}_{j}.Q_in" for j in tanks_id if j != i],
            f"Q_{i}",
        )
        for i in tanks_id
    ]
    + [
        (
            ([f"in_{i}.V_in"] if i in pipes_in_id else [])
            + ([f"out_{i}.V_out"] if i in pipes_out_id else [])
            + [f"pipe_{j}_{i}.V_out" for j in tanks_id if j != i]
            + [f"pipe_{i}_{j}.V_in" for j in tanks_id if j != i],
            f"V_{i}",
        )
        for i in tanks_id
    ],
)
```

And that's it!

```py
S = System(tanks)
S.compile()

S.set_parameters(
    {
        "rate_1_2": 3,
        "rate_2_1": 10,
        "rate_in_1": "Piecewise((4, T<50), (0, True))",
        "rate_in_2": 7,
        "conc_in_1": 1 / 2,
        "conc_in_2": 0,
        "rate_out_1": 11,
        #"rate_out_2": 0
    }
)

print(S)

sym = S.create_simulation(solver="cts", initial_values={"Q_1": 20, "Q_2": 80, "V_1": 800, "V_2": 1000})

sym.simulate(100, n_steps=100)

sym.plot_solution()
```