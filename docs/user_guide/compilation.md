# Compilation

The [definition of a ported object](../mathematics/ported_objects.md) is an object whose ports label and access information inside. 

When a model is build using ported objects, it produces a *formal* object, meaning that instead of producing a ported object to the above definition, it produces an object with the data required to build such an object. *Compilation* is simply the process of forming a ported object with assignments or symbols which are correctly exposed at ports.

The advantage of having a compilation process is that it allows a model to be freely edited, and does not impact the order in which components are specified.

!!! info "This is an automatic process"

    The composition process is entirely automated when creating a system. It should only be called on individual ported objects for testing purposes. 

## Compilation for each ported object

For reference, below is a description of what happens inside each type of ported object.

### Functional ported objects

In functional ported objects, the compilation process associates to each assignment with symbol $S$ an output port `"S"` of the ported object which stores the assignment, and to each free symbol $F$ in the expression of any assignment an input port `"F"` of the ported object.

### Variable ported objects

In variable ported objects, the compilation process first checks that the free symbols in the expression of each assignment are either variables or defined at input ports (which can be automatically, or done by the user). Then: 

- each assignment with symbol $S$ which is to be exposed is stored at a variable port `"S"` of the ported object, 
- each assignment which is not to be exposed is stored as internal information, 
- each free symbol $F$ which is not a variable symbol is associated to an input port `"F"`. 

### Composite ported objects

The compilation process for composite ported objects is slightly more involved. First, each child object is compiled, which results in iterated calls down to the base functional and variable ported objects of a model.

The formal information stored in a composite ported object stores non-trivial information about how different functions and differential equations are to be composed. In particular:

- [Directed wires](../mathematics/functional_substitution.md/#implementation-detail) formally store functional substitutions $\{g_1 \vert_{x_1 = f}, g_2 \vert_{x_2 = f}, \dots, g_k \vert_{x_k = f} \}$ instead of performing them,
- [Variable wires](../mathematics/variable_aggregation.md/#implementation-detail) formally store variable aggregations $(x_1, \dots, x_k) \mapsto y$ instead of performing them.

These are processed as follows.

1. The assignments at the output ports and variable ports of children are collected. Any assignments stored internally in a child are added to the internal storage of the ported object.
2. Directed wires are processed. The three possible cases are:

    1. If the directed wire goes from a child output port to an outport port of the ported object, the assignment at the source port is forwarded to an assignment at the output port. A formal substitution is made for the source symbol and each other destination symbol of the wire to be replaced by the symbol at the output port.

        !!! info "Formal substitution"

            A formal substitution means that the data for the substitution is stored and all substitutions are performed at the end of compilation.

    2. If the directed wire goes from a child output port or child variable port to input ports of other child objects, a formal substitution is made for each destination symbol to be replaced by the source symbol.
    3. If the directed wire goes from an input port of the ported object to input ports of child objects, a formal substitution is made for each destination symbol to be replaced by the source symbol.  

3. Variable wires are processed. If the aggregated variable is to be exposed at a variable port, a formal substitution is made for each child variable symbol to be replaced by the destination symbol and the assignment is stored at the variable port. If the variable is not to be exposed, it is stored as internal information with the specified symbol, which is formally substituted for each child variable symbol.
4. Any inputs of children which have not been connected to are converted to a parameter assignment with their default value, which is stored as internal information (a default value must be defined for such ports, otherwise an exception is raised).
5. Formal subsitutions are performed as actual symbol substitutions.
6. A renaming process prefixing the symbols of all ports and symbols is performed, allowing them to be uniquely referenced in parent ported objects.

!!! info "Internal storage"

    The purpose of internal storage is to protect information. While internal information is forwarded to parent ported objects, it is not updated or accessed.

