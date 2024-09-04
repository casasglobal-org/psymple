# Defining functions

Functions in `psymple` are captured by [functional ported objects](../mathematics/ported_objects.md/#functional-ported-objects). A system of multivariate functions of the form 

$$
\underline{y} = \underline{f}(t, \underline{d})
$$

is captured by a functional ported object with a set of [parameter assignments](../mathematics/variables_parameters.md/#parameter-assignments) modelling $y_i = f_i(t,\underline{d}_i)$ for each $i$, where $\underline{d}_i \subseteq \underline{d}$.

## Example

!!! example "Example: gravitational attraction"

    The magnitude $F$ of the gravitational attraction force between two bodies with spherically-symmetric densities is given by

    $$
    F = G \frac{m_1 m_2}{r^2}
    $$

    where $G$ is the gravitational constant, $m_1$ and $m_2$ are the masses of the two bodies, and $r$ is the scalar distance between their centres of mass.

In `psymple`, this equation can be captured as follows.

``` py title="gravitational force as a FunctionalPortedObject"
from psymple.build import FunctionalPortedObject

f_gravity = FunctionalPortedObject(
    name="f_gravity", # (1)!
    input_ports=["G", "m_1", "m_2", "r"],
    assignments=[("F", "G*m_1*m_2 / (r**2)")],
)
```

1. `name` is used to identify the ports of a system, so should be descriptive and unique.

There are multiple syntaxes for specifying assignments. The following are all equivalent in this example:

=== "tuple input"

    ```py
    assignments = [
        ("F", "G*m_1*m_2 / (r**2)"), 
    ]
    ```

=== "dictionary input"

    ```py
    assignments = [
        dict(parameter="F", expression="G*m_1*m_2 / (r**2)"),
    ]
    ```

=== "`ParameterAssignment` input"

    ```py
    from psymple.build.assignments import ParameterAssignment

    assignments = [
        ParameterAssignment(symbol="F", expression="G*m_1*m_2 / (r**2)"),
    ]
    ```

When `psymple` builds the `f_gravity` functional ported object, it:

1. Builds a `ParameterAssignment` instance for each piece of data in the list `assignments`. In this case it builds the parameter assignment `ParameterAssignment(symbol="F", expression="G*m_1*m_2 / (r**2)")`,
2. Creates the parameter symbol `F`,
3. Creates the set of free symbols `G`, `m_1`, `m_2` and `r`.

Next, it creates input ports as specified by the user. In this case, it matches each element of the specified input ports `["G","m_1","m_2","r"]` to its respective free symbol. It then creates output ports for each assignment: in this case a single output port for the parameter symbol `F`, which can be used to expose the expression `"G*m_1*m_2 / (r**2)"`.

## Next steps

Once functional ported objects are defined, they can be used to [define composite models](composite_ported_objects.md), or [define a simulable system](../user_guide/system.md)

## Notes on best practice

### Automatic port creation

Functional ported objects are able to automatically create input ports. As in the example, `psymple` collects the free symbols from all symbols on the right-hand side of assignments. If the argument `input_ports` is not provided, then every free symbol is exposed as an input port.

Therefore in the example above, it is equivalent to call:

``` py title="gravitational force as a FunctionalPortedObject"
from psymple.build import FunctionalPortedObject

f_gravity = FunctionalPortedObject(
    name="f_gravity",
    assignments=[("F", "G*m_1*m_2 / (r**2)")],
)
```

The automatic creation of input ports can be overridden: see the documentation of [`FunctionalPortedObject`][psymple.build.FunctionalPortedObject] for full details.

### When to specify ports

In practice, the only reason to specify an input port is in the case where a port is to be given a default value, when this should be specified in the `input_ports` argument. In the above example, the gravitational constant $G = 6.67 \times 10^{-11}$ might be assigned. This can still be overridden later in model construction or at simulation. This can be done as follows:

``` py title="gravitational force as a FunctionalPortedObject with default values"
from psymple.build import FunctionalPortedObject

f_gravity = FunctionalPortedObject(
    name="f_gravity",
    input_ports=[("G", 6.67e-11)],
    assignments=[("F", "G*m_1*m_2 / (r**2)")],
)
```

!!! info "System parameters"

    It is also possible to assign meaning to the symbol `G` itself without having to define it through an input port. See [defining a system](../user_guide/system.md).

There are multiple syntaxes for specifying default values at input ports. The following are all equivalent:

=== "tuple input"

    ```py
    input_ports = [("G", 6.67e-11)]
    ```

=== "dictionary input"

    ```py
    input_ports = [
        dict(name="G", default_value=6.67e-11),
    ]
    ```

=== "`InputPort` input"

    ```py
    from psymple.build import InputPort

    input_ports = [
        InputPort(name="G", default_value=6.67e-11),
    ]
    ```

