# Introduction

Differential equations are a core building blocks of a `psymple` system. 

!!! info "Definition"

    A differential equation in `psymple` is a first-order differential equation of the form 
    
    $$ 
    \frac{dx}{dt} = f(x,t,\underline{b}),
    $$
    
    where $\underline{b} = \underline{b}(t)$ are external dependencies. 

Differential equations are stored as a [DifferentialAssignment](docs.assignments.md#differential-assignment) class. In most cases, users will not interact directly with the `DifferentialAssignment` class, since they can be created automatically.

## Example

The logistic model is given by

$$
\frac{dx}{dt} = rx \left( 1-\frac{x}{k} \right)
$$

In `psymple` this equation is captured as follows.

```py title="Logistic equation as a DifferentialAssignment"
from psymple.variables import Variable
from psymple.ported_objects import DifferentialAssignment

pop_x = Variable(symbol="x", 
    initial_value=100, 
    description="Variable for population x",
)

assg_x = DifferentialAssignment(
    symbol_container=pop_x, 
    expression="r*x*(1-x/k)",
)
```

If only the symbol for $x$ needs to be specified, the call for `DifferentialAssignment` can be streamlined.

```py3 title="Logistic equation as a DifferentialAssignment"
from psymple.ported_objects import DifferentialAssignment

assg_x = DifferentialAssignment("x", "r*x*(1-x/k)") # (1)!
```

1. `DifferentialAssignment` accepts the variable and expression as the first and second positional arguments, respectively.
