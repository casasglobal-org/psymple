# Modelling Systems

The package `psymple` implements the building and simulation of temporal dynamical systems models. While the package is designed to allow for the implementation of very general modelling paradigms, it was developed in response to the need for hybrid temporal ecological modelling.

Temporal ecological modelling has classically been approached from two different schools of thought:

1. Mechanistic modelling, in which biological or physical principles are used to capture the flow of energy or resource between different species and systems in order to model population dynamics.
2. Correlative modelling, in which population distribution is modelled as a function of climatic predictor variables such as temperature, humidity and rainfall. 
 
Since biological processes are complex and intricate, mechanistic modelling of ecological systems is not widely persued due to concerns about development time and accuracy. In contrast, correlative modelling is typically derived using multiple regression and machine learning techniques using observational data. 

Correlative modelling has a natural limitation when used for predictive purposes in geographic or climatic ranges outside of the observational data. This becomes a particular concern when, for example, using correlative modelling to predict invasive species potential in new environments.

In response, and with the advances in computing capability, there has been growing interest in hybrid or spectrum models, which compose features of both mechanistic and correlative models. This package is designed to facilitate the construction of these models by easily allowing arbitrary combinations of mechanistic and correlative components.

## Mechanistic and correlative models

### Mechanistic models

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
    \frac{dy}{dt} &= \gamma xy - \delta x
    \end{align}
    $$

    where:

    * $\alpha > 0$ is the birth rate of prey population $x$, 
    * $\delta>0$ is the death rate of predator population $y$, 
    * $\beta>0$ is the predation rate of $y$ on $x$, 
    * $\gamma>0$ is the response rate of $y$ from the predation on $x$.

### Correlative model

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

In `psymple`, spectrum models consistint of building blocks from purely mechanistic models and purely correlative models can be constructed by allowing arbitrary combinations of ordinary differential equations (ODEs) and multivariate functions to be combined together. A system in `psymple` is of the form

$$
\begin{align}
\frac{d \underline{x}}{dt} &= \underline{f}(\underline{x}, \underline{y}, t, \underline{b}) \\
\underline{y} &= \underline{g}(t, \underline{d}) \\
\underline{b} &= \underline{h}(t)
\end{align}
$$



## Principles

`psymple` is built to maximise accessibility and reusability by incorportating the following principles at the core of the design:

### 1. Modular components

Systems of any complexity can be modelled by versatile building blocks called ported objects which can be nested into arbitrary hierarchies to capture the structure of the system being modelled. Each component can be constructed in isolation from the system, while connections from other parts in the system can override default behaviours and capture information or variable flows.

The interface of ported objects and wires provides a separation from the equation systems representing the system. This allows users to focus on the components and interconnectivity of a complex system, while the equation system is automatically built underneath.

### 2. Symbolic systems

The python mathematics library [sympy](https://www.sympy.org/en/index.html) allows for system models to be built, stored and manipulated symbolically. 

1. Clarity: any system component can produce its own system of equations for easy inspection and checking.
2. Dependanbility: models built using computer algebra removes mistakes in combining multiple components.
2. Efficiency: systems built from many parts produce complex equations which can be automatically simplified to aid simulation.

### 3. Data-first design

Systems are built and stored using a flexible data model.

## Examples

