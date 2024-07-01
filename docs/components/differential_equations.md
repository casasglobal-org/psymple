# Introduction

Differential equations, along with functions, are the core building blocks of a `psymple` dynamic system. 

!!! info "Definition"

    A differential equation in `psymple` is a first-order differential equation of the form 
    
    $$ 
    \frac{dy}{dt} = f(y,t,\underline{x}),
    $$
    
    where $\underline{x}$ is a vector of to-be-defined dependencies.

Differential equations are stored as a [DifferentialAssignment](docs.assignments.md#differential-assignment) class

