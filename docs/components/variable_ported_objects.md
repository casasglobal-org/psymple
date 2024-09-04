# Defining ODEs

Differential equations in `psymple` are captured by [variable ported objects](../mathematics/ported_objects.md/#variable-ported-objects). A system of differential equations of the form 

$$ 
\frac{d \underline{x}}{dt} = \underline{f}(\underline{x}, t, \underline{b})
$$

is captured by a variable ported object with a set of [differential assignments](../mathematics/variables_parameters.md/#differential-assignments) modelling $\frac{dx_i}{dt} = f_i (\underline{x}, t, \underline{b}_i)$ for each $i$, where $\underline{b}_i \subseteq \underline{b}$. 

## Example

!!! example "Example: predator-prey system"

    A two-species predator prey system has the form

    $$
    \begin{align}
    \frac{dx}{dt} &= \alpha x - \beta xy \\
    \frac{dy}{dt} &= \gamma xy - \delta y
    \end{align}
    $$

    where:

    * $\alpha>0$ is the birth rate of prey population $x$, 
    * $\delta>0$ is the death rate of predator population $y$, 
    * $\beta>0$ is the predation rate of $y$ on $x$, 
    * $\gamma>0$ is the response rate of $y$ from the predation on $x$.

In `psymple`, this system can be captured as follows.

``` py title="predator-prey as a VariablePortedObject"
from psymple.build import VariablePortedObject

pred_prey = VariablePortedObject(
    name="pred_prey", # (1)!
    input_ports=["a","b","c","d"],
    variable_ports=["x","y"], # (2)!
    assignments=[("x", "a*x - b*x*y"), ("y", "c*x*y - d*y")],
)
```

1. `name` is used to identify the ports of a system, so should be descriptive and unique.

2. Specifying variable ports does not create variables: the variables are created as the left-hand side of the assignments. Variable ports allow the variables created in assignments to be read or updated by other system components.

There are multiple syntaxes for specifying assignments. The following are all equivalent in this example:

=== "tuple input"

    ```py
    assignments = [
        ("x", "a*x - b*x*y"), 
        ("y", "c*x*y - d*y"),
    ]
    ```

=== "dictionary input"

    ```py
    assignments = [
        dict(variable="x", expression="a*x - b*x*y"),
        dict(variable="y", expression="c_x_y - d*y"),
    ]
    ```

=== "`DifferentialAssignment` input"

    ```py
    from psymple.build.assignments import DifferentialAssignment

    assignments = [
        DifferentialAssignment(symbol="x", expression="a*x - b*x*y"),
        DifferentialAssignment(symbol="x", expression="c_x_y - d*y"),
    ]
    ```

When `psymple` builds the `pred_prey` variable ported object, it:

1. Builds a `DifferentialAssignment` instance for each piece of data in the list `assignments`. In this case it builds the differential assignments `DifferentialAssignment(symbol="x", expression="a*x - b*x*y")` and `DifferentialAssignment(symbol="y", expression="c*x*y - d*y")`,
2. Creates variable symbols `x` and `y`,
3. Creates the set of free symbols `a`, `b`, `c` and `d`.

Next, it creates input ports and variable ports as specified by the user. In this case, it matches each element of the specified input ports `["a","b","c","d"]` to its respective free symbol. Similarly, it matches elements of the specified variable ports `["x","y"]` to their respective variable symbols, so that the expressions `"a*x - b*x*y"` and `"c*x*y - d*y"`, respectively, can later be exposed.

## Next steps

Once variable ported objects are defined, they can be used to [define composite models](composite_ported_objects.md), or [define a simulable system](../user_guide/system.md)

## Notes on best practice

### Automatic port creation

Variable ported objects are able to automatically create both input ports and variable ports. As per the example, `psymple` collects the variable symbols from the left-hand side of any assignment, and the free symbols from all symbols on the right-hand side of assignments which are not variable symbols. If the argument `input_ports` is not provided, then every free symbol is exposed as an input port. Similarly, if the argument `variable_ports` is not provided, then every variable symbol is exposed as a variable port.

Therefore in the example above, it is equivalent to call:

``` py title="predator-prey as a VariablePortedObject"
from psymple.build import VariablePortedObject

pred_prey = VariablePortedObject(
    name="pred_prey",
    assignments=[("x", "a*x - b*x*y"), ("y", "c*x*y - d*y")],
)
```

The automatic creation of input ports can be overridden: see the documentation of [`VariablePortedObject`][psymple.build.VariablePortedObject] for full details.

### When to specify ports

In practice, there are only two reasons to specify ports:

1. In the case where not every variable needs to be exposed. This is useful when, for example, a second-order differential equation is being modelled by a system of first-order equations. For example, the pendulum equation $ \ddot y = - \frac{g}{l} sin(y) $ can be written as the two first-order equations $ \dot y = x $ and $ \dot x = - \frac{g}{l} sin(y) $. In this case, we only need to expose the variable `y`. This can be done as follows:

    ``` py title="second-order ODE model"
    from psymple.build import VariablePortedObject

    ode = VariablePortedObject(
        name="second_order_ode",
        variable_ports=["y"],
        assignments=[("y", "x"), ("x", "-g/l * sin(y)")],
    )
    ```

2. In the case where a port is to be given a default value, this should be specified in the `input_ports` argument. In the above example of the pendulum equation, a default value of $ g = 9.81 $ might be assigned. This can still be overridden later in model construction or at simulation. This can be done as follows:

    ``` py title="second-order ODE model with default value"
    from psymple.build import VariablePortedObject

    ode = VariablePortedObject(
        name="second_order_ode",
        input_ports=[("g", 9.81)],
        variable_ports=["y"],
        assignments=[("y", "x"), ("x", "-g/l * sin(y)")],
    )
    ```

There are multiple syntaxes for specifying default values at input ports. The following are all equivalent:

=== "tuple input"

    ```py
    input_ports = [("g", 9.81)]
    ```

=== "dictionary input"

    ```py
    input_ports = [
        dict(name="g", default_value=9.81),
    ]
    ```

=== "`InputPort` input"

    ```py
    from psymple.build import InputPort

    input_ports = [
        InputPort(name="g", default_value=9.81),
    ]
    ```