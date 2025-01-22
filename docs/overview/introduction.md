# Introduction

The following pages give an overview of why `psymple` exists, the problems it tries to address, and how it is designed.

## Roots in ecological modelling

`psymple` was initially designed to deal with complex ecological modelling, where species, or life stages of species, undergo population dynamics, with rates which are often non-trivial composite functions of state variables or time-varying parameters such as environmental, climatic or geographic features.

The difficulty in modelling such systems does not necessarily lie in any one component: population dynamics, interactions or rate models are usually well-understood in isolation. The issues arise when trying to piece together all of the functions or differential equations in a system where multiple species exist, with, for examples subsets of them in competition for resources or predating on each other.

[Read the full statement of need](statement_of_need.md){ .md-button }

## Modular hybrid modelling

`psymple` deals with this problem by allowing each component, be that a population dynamics model, interaction model or rate model, to be considered, built and tested in isolation. This can produce building blocks of reusable components which can then be connected together in a modular and highly general way. These connections automatically build composite functions and complex differential equations in a compilation process which shields the user from the tedious and mistake-prone process of forming equations by hand.

[Modular modelling with functions and differential equations](modelling_systems.md){ .md-button }

## Intended use

This package is primarily a system for building complex system models consisting of multiple (potentially hundreds or thousands) of variables, functions and differential equations. As such, while it can be used as a numerical simulator for systems whose differential equations are known, it is often easier to pass such systems straight to a specialised numerical solver. The strength of `psymple` is being able to produce such simulable systems in cases where it is too time-consuming to do so by hand.

## Modern modelling

`psymple` subscribes to the emerging theory of _collaborative modelling_, the practice of multiple contributors collaborating to build complex systems models. This requires modular, reusable components which naturally fit together, built with clarity and clear records of assumptions, data sources and expertise inputs. 

The collaboration of many domain experts often presents challenges with different technical languages or interpretations of concepts. `psymple` adopts a data-first design for its main objects which allows them to be built from, or dismantled into, wide-ranging formats.

[Read more about the design principles](system_design.md){ .md-button }