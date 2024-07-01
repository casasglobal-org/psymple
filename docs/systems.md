# Modelling Systems

The package `psymple` facilitates the building and simulation of temporal dynamical systems models. It allows for a spectrum of models from purely mechanistic models to purely correlative models to be constructed by allowing arbitrary combinations of ordinary differential equations (ODEs) and multivariate functions to be combined together.

!!! info "Defintion"

    A mechanistic dynamic system model is of the form

    $$ 
    \frac{d \underline{x}}{dt} = \underline{f}(\underline{x}, t, \underline{b})
    $$

    where $\underline{x}$ is a vector of *system states* or *variables*.

## Principles

`psymple` is built to maximise accessibility and reusability by incorportating the following principles at the core of the design:

### 1. Modular components

Systems of any complexity can be modelled by versatile building blocks called ported objects which can be nested into arbitrary hierarchies to capture the structure of the system being modelled. Each component can be constructed in isolation from the system, while connections from other parts in the system can override default behaviours and capture information or variable flows.

The interface of ported objects and wires provides a separation from the equation systems representing the system. This allows users to focus on the components and interconnectivity of a complex system, while the equation system is automatically built underneath.

### 2. Symbolic systems

The python mathematics library [sympy](https://www.sympy.org/en/index.html) allows for system models to be built, stored and manipulated symbolically. 

1. Clarity: any system component can produce its own system of equations for easy inspection and checking.
2. Trust: models built using computer algebra removes mistakes made in building systems out of many parts.
2. Efficiency: systems built from many parts produce complex equations which can be automatically simplified to aid simulation.

### 3. Data-first design

Systems are built and stored using a flexible data model.

## Examples

