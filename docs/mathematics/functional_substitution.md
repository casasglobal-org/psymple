# Functional substitution

Functional substitution, along with [variable aggregation](variable_aggregation.md), are the key components of the composition process in `psymple`.

## Mathematical basis

Functional substitution, also called partial composition, is defined as follows.

!!! info "Definition"

    Given functions \( f: X^n \longrightarrow Z \) and \( g: Y^m \longrightarrow X \), the *partial compositon* of \( f \) with \( g \) at coordinate \( i \) is given by

    $$
    f \vert_{x_i = g} = f(x_1, \dots, x_{i-1}, g(y_1, \dots, y_m), x_{i+1}, \dots, x_n): X^{n-1} \times Y^m \longrightarrow Z.
    $$

## Discussion

In `psymple`, a key assumption is that complex models consist of many substituted or partially composed functions. Returning to [the example of the drag force exerted on a projectile](variables_parameters.md#functions), where the magitude \( F \) was given by

$$
F = \frac{1}{2} \rho C_D A v^2.
$$

The air density, for example, \( \rho \) can itself be a function of air pressure \( P \) and temperature \( T \), and each in turn may be known as functions of spatial geographic coordinates \( (x,y) \) and altitutde \( A \). Similarly, the effective area \( A \) or drag coefficient may be known as a function of geometric parameters \( r_1, \dots, r_k \).

Constructing a static model

$$
F = \frac{1}{2} \rho(P(x,y,A),T(x,y,A)) C_D(r_1,\dots,r_k) A(r_1,\dots,r_k) v^2
$$

including these dependencies is both unclear, since the main components of the force magnitude are lost amongst other functions, and unreusable, since for example the model for air density becomes fixed: changing this model would also require a full resconstruction of the model for \( F \) itself.

## Implementation detail

In `psymple`, functional substitution is stored *formally* by connecting the ports of ported object instances by [`Directedwire`][psymple.build.wires.DirectedWire] instances. A directed wire \( W_d(P_s, D) \) from *source port* \( P_s \) to *destination ports* \( D = \{P_1,\dots,P_k \} \) stores the information associated to functional substitution. Concretely, the source port \( P_s \) exposes an assignment containing an expression, and the destination ports \( D \) expose symbols attached to expressions of other assignments. 

Therefore the directed wire \( W_d(P_s, D) \) represents the functional substitutions

$$
\{g_1 \vert_{x_1 = f}, g_2 \vert_{x_2 = f}, \dots, g_k \vert_{x_k = f} \}
$$

where \( f \) is the expression exposed at \( P_s \), and \( x_i \) is the symbol exposed at \( P_i \in D \) in expression \( g_i \). 

On model compilation, the directed wires in a system are intepreted and the function substitutions performed accordingly. 