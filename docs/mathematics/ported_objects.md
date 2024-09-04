# Ported objects

Ported objects are the core components of how `psymple` functions. 

## Mathematical basis

Abstractly, a ported object is defined as follows.

!!! info "Definition" 

    A *ported object* \( O = O(I, P) \) stores *information* \(I = \{ I_1, \dots, I_m \} \), and *ports* \( P = \{P_1, \dots, P_n \} \) with \( P_i = \{ I_{i_1}, \dots, I_{i_{k_i}} \} \) such that \( P_i \cap P_j = \emptyset \) for all \( i \ne j \) and

    $$
    \bigcup_{i=1}^n P_i = \bigcup_{i=1}^n \{ I_{i_1}, \dots, I_{i_{k_i}} \} \subseteq I.
    $$

    Any \( I_{i_j} \in P_i \) is called *exposed information* and any \( I_k \in I \setminus (P_1 \cup \cdots \cup P_n \) is called *internal information*. 

## Implementation detail

Ported objects in `psymple` are implemented in three layers.

### Base Class

A base class [`PortedObject`][psymple.build.abstract.PortedObject] implementing a ported object object \( O = O(\emptyset, P) \), that is a ported object containing no information but abstractly implementing ports. There are three concrete types of port:

- Variable ports, implemented as [`VariablePort`][psymple.build.ports.VariablePort] instances, which are designed to expose differential equations,
- Input ports, implemented as [`InputPort`][psymple.build.ports.InputPort] instances, which are designed to expose symbols,
- Output ports, implemented as [`OutputPort`][psymple.build.ports.OutputPort] instances, which are designed to expose functions.

### Assignment Containers

Ported objects implementing [variables and parameters](variables_parameters.md), whose information consists of sets of [`Assignment`][psymple.abstract.Assignment] instances and [`sympy.Symbol`](https://docs.sympy.org/latest/modules/core.html#sympy.core.symbol.Symbol) instances. These are abstractly implemented as [`PortedObjectWithAssignments`][psymple.build.abstract.PortedObjectWithAssignments] instances. Concretely, there are:

#### Variable ported objects

Implemented as [`VariablePortedObject`][psymple.build.VariablePortedObject].

These objects are designed to model systems of differential equations as [`DifferentialAssignment`][psymple.build.assignments.DifferentialAssignment] instances. Together, the differential assignments define the following ported object information:

- a set of variable symbols, obtained from the `symbol_wrapper` attribute of each `DifferentialAssignment` instance,
- a set of symbolic rate functions, obtained from the `expression_wrapper` attribute of each `DifferentialAssignment` instance,
- a set of free symbols, defined as the set of all symbols appearing in each symbolic rate function, except those which are variable symbols.

Variable ported objects can be given variable ports, which access the symbolic rate functions accociated to a variable, and input ports, which allow free symbols to be defined externally.

#### Functional ported objects

Implemented as [`FunctionalPortedObject`][psymple.build.FunctionalPortedObject].

These objects are designed to model a collection of multivariate functions as [`ParameterAssignment`][psymple.build.assignments.ParameterAssignment] instances. Together, the parameter assignments define the following ported object information:

- a set of parameter symbols, obtained from the `symbol_wrapper` attribute of each `ParameterAssignment` instance,
- a set of symbolic functions, obtained from the `expression_wrapper` attribute of each `ParameterAssignment` instance,
- a set of free symbols, defined as the set of all symbols appearing in each symbolic rate function.

!!! warning "Note"

    In contrast to variable ported objects, parameter symbols and free symbols must be disjoint. Therefore no symbol appearing on the left-hand side of an assignment can appear on the right-hand side of any assignment. 

Functional ported objects can be given input ports, which allow the free symbols to be defined externally. Output ports are automatically generated from each assignment, which access the symbolic functions associated to each parameter symbol.

### Composite ported objects

Implemented as [`CompositePortedObject`][psymple.build.CompositePortedObject].

These objects implement [functional substitution](functional_substitution.md) and [variable aggregation](variable_aggregation.md) between the functions and differential equations stored in other ported objects contained as children. They can link or expose any information exposed at the ports of any of its children, which means:

- any function exposed at an output port of a child
- any differential equation exposed at the variable port of a child
- any symbol exposed at the input port of a child

Composite ported objects can be given input ports, output ports and variable ports which, when linked by wires to child ports, expose information in the same way as the corresponding ports of child objects.

## Using ported objects

More information about the user-facing ported objects can be found on the following pages:

- [Functional ported objects](../components/functional_ported_objects.md)
- [Variable ported objects](../components/variable_ported_objects.md)
- [Composite ported objects](../components/composite_ported_objects.md)