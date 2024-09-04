# System design

`psymple` is built to maximise accessibility and reusability by incorportating the following principles at the core of the design.

## 1. Modular components

Systems of any complexity can be modelled by versatile building blocks called "ported objects" which can be nested into arbitrary hierarchies to capture the structure of the system being modelled.

These objects can be linked by "wires" which formally represent the flow of resource or information around the system. This provides a degree of separation from the modeller to the dynamically-created system equations, which provides:

1. **Faceted approach**: each component can be conceived, built and tested in isolation from the system.
2. **Diagramatic interface**: complex systems are often visualised through diagrams representing the interconnectivity. The interface to `psymple` is a codified approach to building these diagrams.
3. **Natural interaction**: connections from other parts in the system can override default behaviours and capture information or composite variable dynamics automatically.

## 2. Symbolic systems

The python mathematics library [sympy](https://www.sympy.org/en/index.html) allows for system models to be built, stored and manipulated symbolically. This feature is designed to provide:

1. **Clarity**: any system component can produce its own system of equations for easy inspection and checking.
2. **Dependanbility**: models built using computer algebra removes mistakes in combining multiple components.
2. **Efficiency**: systems built from many parts produce complex equations which can be automatically simplified to aid simulation.

## 3. Data-first design

Systems are built and stored using a flexible `json` data model for its main objects which allows them to be built from, or dismantled into, wide-ranging formats. This is desgined to provide:

1. **Collaborative modelling**: varied domain experts with different technical languages or interpretations of concepts can develop and interact with different interfaces to the core data format. [Read more about collaborative modelling.](https://topos.institute/collaborative-modelling)
2. **Traceability**: a data-centric focus provides a more natural setting to integrate data and assumption sources into the platform for clear and trustable model creation.
3. **Language-agnosticism**: the choice to build `psymple` in `python` is designed to maximise its scalability and uptake. Implementations in other languages may have other advantages, but can be built with the same core data format.
