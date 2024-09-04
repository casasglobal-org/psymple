# Variable aggregation

Variable aggregation, along with [functional substitution](functional_substitution.md), are the key components of the composition process in `psymple`.

## Mathematical basis

Variable aggregation is the process of combining two ordinary differential equations linearly, as follows.

!!! info "Definition"

    Let \( \frac{dx}{dt} = f(x,y,t,\underline{a}) \) and \( \frac{dy}{dt} = g(x,y,t,\underline{b}) \) be differential equations. Their *aggregation under the identification* \( (x,y) \longrightarrow z \) is the differential equation

    $$
    \frac{dz}{dt} = f(z,z,t,\underline{a}) + g(z,z,t,\underline{b}).
    $$

For example:

!!! example "Example"

    The aggreation of the differential equations \( \frac{dx}{dt} = axt +  by + c \) and \( \frac{dy}{dt} = dsin(y) \) under the identification \( (x,y) \longrightarrow z \) is given by 

    $$
    \frac{dz}{dt} = (azt + bz + c) + (dsin(z)).
    $$

## Discussion

In `psymple`, a key assumption is that complex dynamic systems are constructed by aggregating the differential equations of smaller components. For example, consider a tank of water with \( n \) pipes in adding water at rates \( \{r_1,\dots,r_n\} \) and \( m \) pipes out extracting water at rates \( \{s_1,\dots,s_m \} \). Then the rate of change of the volume \( V \) of water in the tank is given by

$$
\frac{dV}{dt} = \sum_{i=1}^n r_i - \sum_{i=1}^m s_i.
$$

If this equation were implemented statically, then adapting the model to account for, for example, a leak whose flow rate is proportional to \( V \), would require writing a completely new differential equation. With the concept of variable aggregation, the contribution equation for \( V \) can instead be considered at each entry and exit point of the tank. For each entry pipe, this is

$$
\frac{dV}{dt} = r_i
$$

and at each exit pipe this is

$$
\frac{dV}{dt} = -s_i.
$$

The original tank model is then the aggregation of all of these component equations. If the leak were to be modelled too, by

$$
\frac{dV}{dt} = -\alpha V
$$

then this can simply be added to the list of variable aggregations to perform.

## Implementation detail

In `psymple`, variable aggregation is stored *formally* by connecting the ports of ported object instances by [`VariableAggregationWiring`][psymple.build.wires.VariableAggregationWiring] instances. A variable aggregation wire \( W_v(C, P_d, I) \) from *child ports* \( C = \{P_1,\dots,P_k \} \) to *destination port* \( P_d \) with *identification variable* \( I \) stores the information associated to variable aggregation. 

Concretely, the child ports \( C \) each expose a differential assignment to be aggregated together, the identification variable \( I \) stores the identification to be made, and the destination port \( P_d \) exposes the aggregated assignment.

On model compilation, the variable aggregation wires in a system are intepreted and the variable aggregations are performed accordingly. 