# Mechanistic and correlative models

This page gives an overview of what is meant by mechanistic and correlative models in the context of `psymple`.

## Mechanistic models

Mechanistic models are dynamic models in which the evolution of the system is specified as a system of first-order ordinary differential equations (ODEs). 

!!! info "Defintion: mechanistic model"

    A mechanistic dynamic system model is of the form

    $$ 
    \frac{d \underline{x}}{dt} = \underline{f}(\underline{x}, t, \underline{b})
    $$

    where $\underline{x} = \underline{x}(t)$ are *system states* or *variables* and $\underline{b} = \underline{b}(t)$ are *external dependencies*. 

A familiar example of a mechanistic model is the Lotka-Volterra or predator-prey system.

!!! example "Example: predator-prey system"

    A two-species predator prey system has the form

    $$
    \begin{align}
    \frac{dx}{dt} &= \alpha x - \beta xy \\
    \frac{dy}{dt} &= \gamma xy - \delta y
    \end{align}
    $$

    where:

    * $\alpha > 0$ is the birth rate of prey population $x$, 
    * $\delta>0$ is the death rate of predator population $y$, 
    * $\beta>0$ is the predation rate of $y$ on $x$, 
    * $\gamma>0$ is the response rate of $y$ from the predation on $x$.

## Correlative models

A correlative model is a general term for a model in which the evolution is specified explicitly in terms of time and the system states.

!!! info "Definition: correlative model"

    A correlative model is of the form

    $$
    \underline{y} = \underline{f}(t, \underline{d})
    $$

    where $\underline{y} = \underline{y}(t)$ is a vector of *system states* and $\underline{d} = \underline{d}(t)$ are *external dependencies*.

Correlative models can be used to approximate the behaviour of a system component with other system states.

!!! example "Example: correlative ecological niche models"

    Data may be used to model the prevalance of a certain species $y$ in response to temporal climatic features such as temperature $T$, relative humitidy $H_r$ and precipitation $P$. In this case the model will have the form

    $$
    y(t) = f(T, H_r, P)
    $$

    where $T=T(t)$, $H_r = H_r(t)$ and $P=P(t)$ are known in terms of $t$.


## Spectrum models

In `psymple`, spectrum models consistint of building blocks from purely mechanistic models and purely correlative models can be constructed by allowing arbitrary combinations of ordinary differential equations (ODEs) and multivariate functions to be combined together. A system in `psymple` is therefore of the form:

$$
\begin{align}
\frac{d \underline{x}}{dt} &= \underline{f}(\underline{x}, \underline{y}, t, \underline{b}) \\
\underline{y} &= \underline{g}(t, \underline{d}) \\
\underline{b} &= \underline{h}(t)
\end{align}
$$

## Up next:

[System design](system_design.md)