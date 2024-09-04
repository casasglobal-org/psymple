# Defining composite models

A composite model consists of collections of functions and differential equations composed together by [functional substitution](../mathematics/functional_substitution.md) and [variable aggregation](../mathematics/variable_aggregation.md). Composite models in `psymple` are captured by [composite ported objects](../mathematics/ported_objects.md/#composite-ported-objects).

The functions and differential equations to be composed come from ported objects added as children. The ports of these child objects are then connected to the ports of the parent ported object by [directed wires](../mathematics/functional_substitution.md/#implementation-detail) to capture functional substitution, and [variable wires](../mathematics/variable_aggregation.md/#implementation-detail) to capture variable aggregation.

!!! info "Functions and differential equations"
    
    First read how to [define functions](functional_ported_objects.md) and [define ODEs](variable_ported_objects.md) as ported objects in `psymple`.

## Example

A very simple problem which can be modelled in a composite ported object is the following.

!!! example "Example: projectile with air resistance"

    Consider an object dropped from a height $h$ at time $t=0$. The object falls vertically downwards under the force of gravity with speed $v(t)$, and is acted on by air resistance with magnitude

    $$
    \frac{1}{2}C_D \rho A v^2
    $$

    directed vertically upwards, where $C_D$ is the drag coefficient of the object, $\rho$ is the air denstity, $A$ is the effective surface area of the object, and $m$ is its mass.

In `psymple`, the forces acting on the falling object can be modelled individually, and then aggregated together. Let the positive direction be downwards. For the gravitational force $F_G = mg$, applying Newton's second law gives $\frac{dv}{dt} = g$, while for the resistance force, $\frac{dv}{dt} = - \mu v^2$, where $\mu = \frac{C_D \rho A}{2m}$. 

The following three ported objects capture the two dynamic components, and the multiplier $\mu$. See [defining functions](functional_ported_objects.md) and [defining ODEs](variable_ported_objects.md) for more detail.

```py title="falling object - components"
from psymple.build import FunctionalPortedObject, VariablePortedObject

v_gravity = VariablePortedObject(
    name="v_gravity",
    input_ports=[("g", 9.81)], # (1)!
    assignments=[("v", "g")],
)

v_drag = VariablePortedObject(
    name="v_drag",
    assignments=[("v", "-mu * v**2")], # (2)!
)

f_drag = FunctionalPortedObject(
    name="f_drag",
    assignments=[("mu", "C * rho * A / (2 * m)")], # (3)!
)
```

1. The default $g=9.81$ is specified here so that we don't need to worry about it later.

2. This assignment automatically creates an input port `"mu"` and variable port `"v"` of `"v_drag"` to connect to.

3. This assignment automatically creates input ports `["C", "rho", "A", "m"]` and an output port "`mu`" of `"f_drag"` to connect to.

To create the falling object model from these components, `psymple` needs to know:

1. That the variable at port `"v"` of `"v_gravity"` and the variable at port `"v"` of `"v_drag"` need to be aggregated,
2. That the input `"mu"` of `"v_drag"` needs to read the output value `"mu"` of `"f_drag"`,
3. How to obtain the values of the inputs `["C", "rho", "A", "m"]` of `"f_drag"`. 

!!! info "Referencing a child port"

    The port of a child object is referenced by the string `"name.port_name"` where `name = child.name` is the attritube specified when instantiating that child object. This *does not* need to be the same as the `python` identifier.

These are all accomplished inside this composite ported object:

```py title="falling object - model"
from psymple.build import CompositePortedObject

model = CompositePortedObject(
    name="model",
    children=[v_gravity, v_drag, f_drag], # (1)!
    input_ports=["C", "rho", "A", "m"],  # (2)!
    variable_ports=["v"], # (3)!
    directed_wires=[
        ("C", "f_drag.C"), # (4)!
        ("rho", "f_drag.rho"),
        ("A", "f_drag.A"),
        ("m", "f_drag.m"),
        ("f_drag.mu", "v_drag.mu"), # (5)! 
    ],
    variable_wires=[
        (["v_gravity.v", "v_drag.v"], "v") # (6)!
    ],
)
```

1. This imports the three ported objects from before into `"model"` so that their ports and assignments can be accessed.

2. This creates a list of inputs, or model dependencies, on the outside of `"model"`. Adjusting these will change the behaviour of the model.

3. This creates a variable port `"v"` for `"model"` which will access the velocity of the object.

4. This tuple tells `psymple` to identify the value at input `"C"` with the value of `"C"` inside the assignment of `"f_drag"`. Similarly for the next three tuples.
 
5. This tuple tells `psymple` to identify input `"mu"` of `"v_drag"` with the output value `"mu"` of `"f_drag"`.

6. This tuple tells `psymple` to aggregate the variable at port `"v"` of `"v_gravity"` and the variable at port `"v"` of `"v_drag"` together, and expose the aggregated variable at the variable port `"v"` of `"model"`.

There are two syntaxes for specifying directed wires. The following are equivalent in this example:

=== "tuple input"

    ```py
    directed_wires=[
        ("C", "f_drag.C"), 
        ("rho", "f_drag.rho"),
        ("A", "f_drag.A"),
        ("m", "f_drag.m"),
        ("f_drag.mu", "v_drag.mu"), 
    ],
    ```

=== "dictionary input"

    ```py
    directed_wires=[
        {"source": "C", "destination": "f_drag.C"}, 
        {"source": "rho", "destination": "f_drag.rho"},
        {"source": "A", "destination": "f_drag.A"},
        {"source": "m", "destination": "f_drag.m"},
        {"source": "f_drag.mu", "destination": "v_drag.mu"}, 
    ],
    ```

Similarly, there are two syntaxes for specifying variable wires. The following are equivalent:

=== "tuple input"

    ```py
    variable_wires=[
        (["v_gravity.v", "v_drag.v"], "v") 
    ],
    ```

=== "dictionary input"

    ```py
    variable_wires=[
        {
            "child_ports": ["v_gravity.v", "v_drag.v"],
            "parent_port": "v",
        }
    ],
    ```

When `psymple` builds the `model` composite ported object, it:

1. Creates the input ports and variable ports specified.
2. Builds a [`DirectedWire`][psymple.build.wires.DirectedWire] instance for each itme in the argument list `directed_wires`. In doing so, it checks that all the ports exist and are of the correct type (source ports must be input ports of `model`, or output ports/variable ports of its children, and destination ports must be input ports of children, or output ports of `model`).
3. Builds a [`VariableAggregationWiring`][psymple.build.wires.VariableAggregationWiring] instance for each item in the argument list `variable_wires`. In doing so, it checks all the ports exist and are variable ports.

## Next steps

Once models are defined using composite ported objects, they can be used to [define a simulable system](../user_guide/system.md)

## Notes on best practice

### Arbitrary nesting

Composite ported objects can have other composite ported objects as children. This allows for arbitrarily complex nested structures to be built, which can reflect system hierarchies. 

### Automatic port creation

Currently, ports are not automatically created in `CompositePortedObject` instances. A common source of errors is either a child not being added to an object, or not manually creating a port. 

A future update may support automatic port creation when wires with external ports are specified, along with easing the process of forwarding inputs into children.





