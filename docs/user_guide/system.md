# Creating a system

A [`System`][psymple.build.System] translates a model defined in a ported object into a system which can be simulated. In doing so, it provides *context* to the model, by telling it how to concretely interpret certain symbols and functions.

## Contextualisation

The process of telling a model how to interpret symbols and functions is called *contextualisation*. There are three things that a system can contextualise:

- **time**: the symbol which represents the independent system variable which is simulated over,
- **utility functions**: which provide a system-wide definition of a function call,
- **system parameters**: which provide a system-wide definition of a symbol.

The default symbol for time is `T`. When used in an assignment in a ported object, it is automatically not interpreted as a free symbol, and does not need associated ports to be defined.

### Automatic parsing from `sympy`

Before getting to utility functions and system parameters, it is helpful to know that all assignments provided in `str` format in `psymple` are parsed using [`sympy.parse_expr`](https://docs.sympy.org/latest/modules/parsing.html#sympy.parsing.sympy_parser.parse_expr). This accounts for a large number of common functions, most commonly:

- [Trigonometric functions](https://docs.sympy.org/latest/modules/functions/elementary.html#trigonometric-functions) such as `sin` and `cos`, and their [inverses](https://docs.sympy.org/latest/modules/functions/elementary.html#trigonometric-inverses), 
- [Hyperbolic functions](https://docs.sympy.org/latest/modules/functions/elementary.html#hyperbolic-functions) such as `sinh` and `cosh` and their [inverses](https://docs.sympy.org/latest/modules/functions/elementary.html#hyperbolic-inverses),
- [Mathematical functions](https://docs.sympy.org/latest/modules/functions/elementary.html#miscellaneous) such as `Min`, `Max`, `root` and `sqrt`,
- [Integer functions](https://docs.sympy.org/latest/modules/functions/elementary.html#integer-functions) such as `floor` and `ceiling`,
- [Exponentials and logarithms](https://docs.sympy.org/latest/modules/functions/elementary.html#exponential),
- [Piecewise functions](https://docs.sympy.org/latest/modules/functions/elementary.html#piecewise).

For example, writing the strings `"sin(x)"` or `"log(x)"` in assignments are interpreted as the symbolic functions `sin(x)` and `log(x)`, respectively. 

Certain symbols are also interpreted automatically. The full list of these is `['O', 'Q', 'N', 'I', 'E', 'S', 'beta', 'zeta', 'gamma', 'pi']`, and point to functions, constants, or other information in `sympy`. 

!!! warning "Single letter variables in `psymple`"

    There is currently no way of overriding the single symbols `['O', 'Q', 'N', 'I', 'E', 'S']` in `psymple`, and using them in assignments can lead to unexpected behaviour. It is best to avoid using these symbols in `psymple`, unless you are using them for their purpose in `sympy`. A planned feature will help deal with these symbols.

### Utility functions

Utility functions supplement the functions that can already be interpreted by `sympy`. They can be simple, such as small `lambda` functions, or perform complex tasks, such as fetching information from data frames. In general, *any* callable function returning a single `float` value can be specified as a utility function.

!!! example "A simple lambda function"

    A common function which becomes useful is ensuring simulations don't fail from division-by-zero. The function $\mathrm{frac}_0$ is defined by

    $$
    \mathrm{frac}_0(a,b,d) = \begin{cases} \frac{a}{b}, & b \ne 0, \\ d, & b = 0. \end{cases}
    $$

Adding $\mathrm{frac}_0$ to a system is done as follows:

```py title="Adding a callable utility function"
from psymple.build import System

frac_0 = lambda a,b,d: a/b if b != 0 else d

S = System()
S.add_utility_function(name="frac_0", function=frac_0) # (1)!
```

1. Like all `psymple` objects, the parameter `name` specifies how the object, in this case the function, is called in string inputs. 

Then, whenever `"frac_0(x,y,z)"` is used in an assignment, it is recognised as a symbolic function, and interpreted at the lambda function `frac_0` at simulation. 

!!! info "Function arguments"

    When adding a callable function as above, `psymple` determines the number of inputs the function should be provided. In the above example, enterting `"frac_0(x,y)"` in an assignment will raise an error because the lambda function `frac_0` cannot be interpreted with just two arguments.

    **Currently, default arguments, position-only arguments and keyword-only arguments are not fully supported. This is a planned feature.**

It is also possible to specify utility functions by specifying their symbolic representation. For example, a model temperature function $temp(t) = 10sin(t) + 20$ can be added as follows:

```py title="Adding a symbolic utility function"
from psymple.build import System

S = System()
S.add_utility_function(name="temp", function="10*sin(T) + 20") # (1)!
```

1. By default, time is represented by symbol `T`.

For more information on adding utility functions and syntax, see [`add_utility_function`][psymple.build.system.FunctionHandler.add_utility_function].

### System parameters

System parameters are similar to utility functions, except they specify how certain symbols should be interpreted. A system parameter can represent a constant, such as the standard gravity constant on Earth is $g=9.81$, or can be a function, whose arguments must be either:

- the system variable time,
- already existing system parameters.

!!! info "System parameters and input ports"
    System parameters "win" over input ports of a ported object. If a system parameter `"P"` is specified and a port `"P"` is specified in a ported object, the port `"P"` will not be created, and a warning will be issued.

Adding a system parameter to a system is similar to adding a utility function. For example, specifying the standard gravity constant can be done as follows:

```py title="Standard gravity"
from psymple.build import System

S = System()
S.add_system_parameter("g", 9.81)
```

Then, whenever `"g"` is used in an assignment, it is recognised as a system parameter, and interpreted as $9.81$ during simulation.

As a second example suppose there are callable functions `t_max` and `t_min` which fetch the maximum and minimum temperature, respectively, on a given day from a dataframe of climate data. Since these only depend on time, they can be interpreted as system parameters as follows.

```py title="Maximum and minimum temperatures"
from psymple.build import System

def t_max(t) -> float:
    ...

def t_min(t) -> float:
    ...

S = System()
S.add_system_parameter(name="T_MAX", function=t_max, signature=("T",)) # (1)!
S.add_system_parameter(name="T_MIN", function=t_min, signature=("T",))
```

1. The argument `signature=("T",)` tells `psymple` that the system time symbol `T` should always be passed to `t_max`.

Now that `"T_MAX"` and `"T_MIN"` are system parameters, additional system parameters can be defined based on their values. For example, the parameter `T_AVG = (T_MAX + T_MIN)/2` is defined as follows:

```py title="Average temperature"
S.add_system_parameter(
    name="T_AVG", 
    function="(T_MAX + T_MIN)/2", 
    signature=("T_MAX", "T_MIN"), # (1)!
) 
```

1. The argument `signature=("T_MAX", "T_MIN")` tells `psymple` the order in which arguments should be displayed. It doesn't affect computation.

For more information on adding system parameters and syntax, see [`add_system_parameter`][psymple.build.system.FunctionHandler.add_system_parameter].

## Setting the system object

Once a system exists, a ported object can be imported and [compiled](compilation.md) in the context of the system. The goal of this process is to produce:

- A set of differential equations, one describing the evolution of each variable after compilation.
- A set of functions which define dependencies in the differential equations in terms of variables and, recursively, other functions.

These two collections define a *simulable system*, which can be solved proceedurally (not implemented), or numerically once all the dependencies have been substituted in terms of system variables.

### Example

In the following example, this [model of an object falling vertically, subject to gravitational and air resistance forces](../components/composite_ported_objects.md/#example), is considered. The code can also be found by expanding the following block.

??? example "Falling object example"

    ```py title="Falling object with air resistence"
    from psymple.build import (
        FunctionalPortedObject, 
        VariablePortedObject,
        CompositePortedObject,
    )

    v_gravity = VariablePortedObject( # (1)!
        name="v_gravity",
        assignments=[("v", "g")], 
    )

    v_drag = VariablePortedObject(
        name="v_drag",
        assignments=[("v", "-mu * v**2")],
    )

    f_drag = FunctionalPortedObject(
        name="f_drag",
        assignments=[("mu", "frac_0(1/2 * C * rho * A, m, 0)")], # (2)!
    )

    model = CompositePortedObject(
        name="model",
        children=[v_gravity, v_drag, f_drag],
        input_ports=["C", "rho", "A", "m"],
        variable_ports=["v"],
        directed_wires=[
            ("C", "f_drag.C"),
            ("rho", "f_drag.rho"),
            ("A", "f_drag.A"),
            ("m", "f_drag.m"),
            ("f_drag.mu", "v_drag.mu"), 
        ],
        variable_wires=[
            (["v_gravity.v", "v_drag.v"], "v")
        ],
    )    
    ```

    1. The default input port for `"g"` has been removed. This will be replaced with a system parameter.
    2. The drag force is calculated using `frac_0`, see [here](#utility-functions), to allow for massless objects.

The model has two changes:

1. The default input port for `"g"` has been removed. This will be replaced with a system parameter.
2. The drag force is calculated using `frac_0`, see [here](#utility-functions), to allow for massless objects. A system will tell `psymple` how to interpret this function using a utility function.

```py title="Falling object system"
from psymple.build import System

frac_0 = lambda a,b,d: a/b if b != 0 else d

S = System()
S.add_utility_function(name="frac_0", function=frac_0)
S.add_system_parameter(name="g", function=9.81)

S.set_object(model)
```

The call `S.set_object(model)`:

1. Imports the ported object `model` into the system.
2. [Compiles](./compilation.md) it, and its child objects.
3. Produces simulable variables and parameters.

### Inspecting the system

To get an idea of what was produced, once an object is added to a system, `print` can be called.

!!! info "System inspection"

    Features for inspecting a system are not fully developed. Calling `print` is the easiest way of what is going on. More information can be gathered from inspecting the objects in the dictionaries `S.variables` and `S.parameters`. 

```py title="Printing a system output"
>>> print(S)
system ODEs: ['dx_0/dt = -a_0*x_0**2 + g()'] 
system functions: ['a_0 = frac_0(a_1*a_2*a_3/2, a_4, 0)', 'a_1 = REQ', 'a_2 = REQ', 'a_3 = REQ', 'a_4 = REQ']
variable mappings: {v: x_0, T: t}
parameter mappings: {f_drag.mu: a_0, C: a_1, rho: a_2, A: a_3, m: a_4}
```

The first two lines of the output give the ODEs and functions, respectively. The second two lines give mappings between the system identifiers and the "readable symbols" in the first two lines. Combining the above information the system is given by:

$$
\frac{dv}{dt} = g -\mathrm{frac_0}\left( \frac{1}{2}C\rho A, m, 0 \right) v^2 = \begin{cases} g - \frac{C \rho A}{2m} v^2, & m \ne 0, \\ g, & m=0 \end{cases}
$$

The outputs `'a_1 = REQ', 'a_2 = REQ', 'a_3 = REQ', 'a_4 = REQ'` indicate that the values of $C$, $\rho$, $A$ and $m$ are required before simulation can occur.

### Setting input parameters

Setting parameter values is possible using the [`set_parameters`][psymple.simulate.simulation.SetterObject.set_parameters] method. Staying with the previous example:

```py title="Setting input parameters"
S.set_parameters({"C": 1.1, "rho": 1, "A": 0.2, "m": 2})
```

Now printing:

```py
>>> print(S)
system ODEs: ['dx_0/dt = -a_0*x_0**2 + g()']
system functions: ['a_0 = frac_0(a_1*a_2*a_3/2, a_4, 0)', 'a_1 = 1.10000000000000', 'a_2 = 1', 'a_3 = 0.200000000000000', 'a_4 = 2']
variable mappings: {v: x_0, T: t}
parameter mappings: {f_drag.mu: a_0, C: a_1, rho: a_2, A: a_3, m: a_4}
```

Now all the parameters have been set correctly.

## Simulating the system

Once a system has been created with a ported object, it can be [simulated](simulation.md).

