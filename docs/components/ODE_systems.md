# Introduction

Systems of ordinary differential equations (ODEs) capture dynamic mechanistic models. 

!!! info "Defintion: mechanistic model"

    A mechanistic dynamic system model is of the form

    $$ 
    \frac{d \underline{x}}{dt} = \underline{f}(\underline{x}, t, \underline{b})
    $$

    where $\underline{x} = \underline{x}(t)$ are *system states* or *variables* and $\underline{b} = \underline{b}(t)$ are *external dependencies*. 

Systems of ODEs are stored as a `VariablePortedObject` class. These ported objects store a set of ODEs, each an instance of the `DifferentialAssignment` class, and can expose the following ports:

- `InputPort`, capturing the external dependencies $\underline{b}$,
- `VariablePort`, which expose one of the variables $\underline{x}$.

The `VariablePortedObject` class is a key user-facing class.

# Example

Consider the following predator-prey system.

!!! example "Example: predator-prey system"

    A two-species predator prey system has the form

    $$
    \begin{align}
    \frac{dx}{dt} &= \alpha x - \beta xy \\
    \frac{dy}{dt} &= \gamma xy - \delta x
    \end{align}
    $$

    where:

    * $\alpha > 0$ is the birth rate of prey population $x$, 
    * $\delta>0$ is the death rate of predator population $y$, 
    * $\beta>0$ is the predation rate of $y$ on $x$, 
    * $\gamma>0$ is the response rate of $y$ from the predation on $x$.

In `psymple`, this system can be captured as follows.

``` py title="predator-prey as a VariablePortedObject"
from psymple.ported_objects import VariablePortedObject

pred_prey = VariablePortedObject(
    name="pred_prey",
    input_ports=["a","b","c","d"],
    variable_ports=["x","y"], # (1)!
    assignments=[("x", "a*x - b*x*y"), ("y", "c*x*y - d*x")],
)
```

1. Specifying variable ports does not create variables: the variables are created as the left-hand side of the assignments. Variable ports allow the variables created in assignments to be read or updated by other system components.

In this form, the parameters $a$, $b$, $c$ and $d$ are required inputs. To specify default values, a list of tuples, dictionaries or `InputPort` instances can be passed to the `input_ports` parameter. The following would be equivalent calls in this case:

=== "tuple input"

    ```py
    input_ports = [("a", 10), ("b", 20), ("c", 15), ("d", 5)]
    ```

=== "dictionary input"

    ```py
    input_ports = [
        dict(name="a", default_value=10),
        dict(name="b", default_value=20),
        dict(name="c", default_value=15),
        dict(name="d", default_value=5),
    ]
    ```

=== "`InputPort` input"

    ```py
    from psymple.ported_objects import InputPort

    input_ports = [
        InputPort(name="a", default_value=10),
        InputPort(name="b", default_value=20),
        InputPort(name="c", default_value=15),
        InputPort(name="d", default_value=5),
    ]
    ```