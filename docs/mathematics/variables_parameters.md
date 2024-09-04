# Variables, parameters and equations

## Mathematical basis

The core purpose of `psymple` is to build simulable dynamic systems from components of functions and differential equations. These components have concrete mathematical definitions:

!!! info "Definition"

    A *mathematical variable* \( x \) is a system state whose time-derivative can be expressed as a function of itself, time, and external dependencies:

    $$
    \frac{dx}{dt} = f(x, t, \underline{b})
    $$

Here, *external dependency* can mean any other system variable, parameter (see below), or constant.

!!! info "Defintion"

    A *mathematical parameter* \( p \) is a state whose value can be expressed as a function of time, and external dependencies:

    $$
    p = f(t, \underline{b})
    $$

## Implementation detail

We notice the similarity of these definitions is that they each consist of an object (respectively a derivative or a symbol) on the left-hand side of an equality, and a function on the right-hand side. To store these concepts flexibly, `psymple` implements the following objects:

### Variables

[`Variable`][psymple.variables.Variable] instances store a [`sympy.Symbol`](https://docs.sympy.org/latest/modules/core.html#sympy.core.symbol.Symbol) instance which is formally interpreted as a first-order time derivative of that symbol.

### Parameters

[`Parameter`][psymple.variables.Parameter] instances store a `sympy.Symbol` instance.

### Expression wrappers

[`ExpressionWrapper`][psymple.abstract.ExpressionWrapper] instances store a symbolic representation of a function, which can be any object subclassed from the [`sympy.Basic`](https://docs.sympy.org/latest/modules/core.html#sympy.core.basic.Basic) class.

### Differential assignments

[`DifferentialAssignment`][psymple.build.assignments.DifferentialAssignment] instances store a `Variable` instance together with an `ExpressionWrapper` instance to formally represent a differential equation of the form

$$
\frac{dx}{dt} = f(x, t, \underline{b})
$$

### Parameter assignments 

[`ParameterAssignment`][psymple.build.assignments.ParameterAssignment] instances store a `Parameter` instance together with an `ExpressionWrapper` instance to formally represent an equation 

$$
p = f(t, \underline{b})
$$

## Example usage

!!! warning "Warning"

    These objects are abstract objects for formal storage. In normal usage of `psymple`, none of these classes need to be explicitly instantiated, since there are interfaces to ease their creation. The examples below give a flavour of how `psymple` works underneath.

### Differential equations

The logistic model is given by

$$
\frac{dx}{dt} = rx \left( 1-\frac{x}{k} \right)
$$

In `psymple` this equation is captured as follows.

```py title="Logistic equation as a `DifferentialAssignment`"
from psymple.build.assignments import DifferentialAssignment

assg_x = DifferentialAssignment(
    symbol="x", 
    expression="r*x*(1-x/k)",
)
```

The `DifferentialAssignment` class has attributes `symbol_wrapper` and `expression_wrapper` which store created instances of `Variable` and `ExpressionWrapper`, respectively. The creation of the `sympy.Symbol` instance and the parsing of the `expression` argument into a `sympy` expression is automatically performed.

### Functions

The magnitude \( F \) of the drag force exerted on a projectile travelling through a medium is given by

$$
F = \frac{1}{2} \rho C_D A v^2
$$

where \( \rho \) is the medium density, \( C_D \) is the drag coefficient, \( A \) is the effective surface area and \( v \) is the speed of the projectile relative to the medium. In `psymple`, this is captured as follows.

```py title="Drag equation as a `ParameterAssignment`"
from psymple.build.assignments import ParameterAssignment

assg_F = ParameterAssignment(
    symbol="F",
    assignment="1/2 * rho * C_D * A * v**2"
)
```

Similar to above, the `ParameterAssignment` class has attributes `symbol_wrapper` and `expression_wrapper` which store created instances of `Parameter` and `ExpressionWrapper`, respectively.