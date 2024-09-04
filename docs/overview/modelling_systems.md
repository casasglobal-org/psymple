# Hybrid systems modelling

The package `psymple` implements the building and simulation of temporal dynamical systems models. While the package is designed to allow for the implementation of very general modelling paradigms, it was developed in response to the need for hybrid temporal ecological modelling.

## Some background in ecological modelling

Temporal ecological modelling has classically been approached from two different schools of thought:

1. **Mechanistic modelling**, in which biological or physical principles are used to capture the flow of energy or resource between different species and systems in order to model population dynamics.
2. **Correlative modelling**, in which a population distribution or other factor such as a suitability index is modelled as a function of climatic, environmental or geographic predictor variables such as temperature, rainfall, soil type or altitude.
 
Since biological processes are complex and intricate, mechanistic modelling of ecological systems is not widely persued due to concerns about development time and accuracy. In contrast, correlative modelling is typically derived using multiple regression or machine learning techniques, requiring few variables and allowing for rapid assessments.

## Hybrid modelling

Correlative modelling, however, has a natural limitation when used for predictive purposes in geographic or climatic ranges outside of the observational data. This becomes a particular concern when, for example, using correlative modelling to predict invasive species potential in new environments.

In response, and with the advances in computing capability, there has been growing interest in hybrid or spectrum models, which compose features of both mechanistic and correlative models. This package was initially desgined to facilitate the construction of these models by easily allowing arbitrary combinations of mechanistic and correlative components.

## Up next:

[Mechanistic and correlative modelling](modelling_types.md)