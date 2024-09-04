---
title: 'Psymple: A Python package for complex systems modelling'
authors:
  - name: George Simmons
    orcid: 0000-0002-9076-4973
    corresponding: true
    affiliation: 1
  - name: David Stern
    affiliation: 1
  - name: Georg Osang
    orcid: 0000-0002-8882-5116
    affiliation: 1
  - name: Luigi Ponti
    orcid: 0000-0003-4972-8265
    affiliation: "2, 3"
  - name: Chiara Facciolà
    orcid: 0000-0001-8359-9300
    affiliation: 1

affiliations:
 - name: IDEMS International CIC, Reading, United Kingdom
   index: 1
 - name: Agenzia nazionale per le nuove tecnologie, l’energia e lo sviluppo economico sostenibile (ENEA),
Centro Ricerche Casaccia, Via Anguillarese 301, 00123 Rome, Italy
   index: 2
  - name: Center for the Analysis of Sustainable Agricultural Systems, 37 Arlington Ave, Kensington,
CA 94707-1035, USA
   index: 3
date: 04 September 2024
bibliography: paper.bib
---

# Summary

The modelling of complex systems, those systems characterised by high degrees of interdependence amongst components, is continually evolving in response to developing computing and visualisation power. Examples such as ecological, economic or social systems are classically modelled using statistical or correlative techniques, which have natural shortcomings when used for predictive modelling outside of the range of their parametrisation data.

Predictive modelling is improved by mechanistic models which deterministically capture the evolution of a system, or hybrid models consisting of mechanistic and correlative components. These models often feature significantly increased size and complexity, and there has been a growing requirement for so-called next generation modelling platforms which are built to a specification requiring modular and data-first implementations which drive clear, adaptable, reusable and accessible modelling practices.

The platform `psymple` is designed to facilitate the development of hybrid complex system models and modelling frameworks. It allows users to link together arbitrary combinations of modular mechanistic and functional components to build categorical diagrams representing a complex system. A compilation process automatically generates simulable system equations from these diagrams using symbolic mathematics package `sympy`. Ultimately, this allows users to focus on the components and interactions of models, rather than their complex equation structure. 

# Statement of need

The development of `psymple` emerged from the complex system modelling requirements of ecological systems. Ecological niche models, also called species distribution models (SDMs) predict species distributions in response to geographic and climatic features [@el-fr:2017; @el-le:2009]. These models are classically formed using correlative or statistical approaches which match observational data to a set of environmental variables to produce favorability ranges for each species.

An alternative approach to SDM is known as mechanistic modelling, which uses physiological species data to parametrise population dynamics models which respond to environmental inputs [@ke-po:2009]. Mechanistic SDMs decouple the physiology of a species from their geographic and climatic environment, and allow species distribution models which respond to environmental or climatic change to be created in the absence of observational data [@john:2019].

More generally, these approaches can be respectively summarised as correlative and mechanistic approaches to complex systems modelling. Classically, the choice between these approaches is often decided based on resource, expertise, or data constraints. More recently, the development of models sitting between the extremes the of correlative and mechanistic approaches, which use components and ideas from both, has been considered [@buck:2010; @to-va:2023]. These approaches are referred to as hybrid or spectrum models.

An example hybrid framework in ecological modelling is physiologically-based demographic modeling (PBDM), which uses physiological data to parametrise functions capturing biophysical or biochemical mechanisms, for example, the development, mortality and fecundity rates of a species in response to environmental variables (see [@po-gu:2023] for an overview and references).  The PBDM approach highlights the considerable advantages of mechanistic SDMs, such as being able to consider the effects of tritrophic ecosystem interactions [@g-y-n-e:1999], while retaining the comparable ease of parametrisation as status-quo correlative models. 

The barrier to produce widespread mechanistic or hybrid complex system models is often cited as the lack of available modelling frameworks [@bu-c-j:2018], the lack of flexibility in existing models [@buck:2010], or the lack of modelling platforms to implement existing ideas [@po-gu:2023]. 

The package `psymple` is a general modelling platform designed to facilitate the creation of hybrid complex systems models. It is built to a specification shared by "next-generation" dynamical systems modelling frameworks, see [@baez:2023], including being open-source, modular and data-first to drive clear, adaptable and accessible modelling practices. These ideas allow for legible modelling of highly complex, specialised systems, and allow for low- or no-code interfaces to improve utilisation amongst non-specialist users. Modular structures pave the way for cross-platform integrations, and a data structure abstracted from modelling objects promotes reuse and flexibility. 

Models are built from arbitrary combinations of modular mechanistic, dynamic components and correlative, functional components which naturally interact with each other. In doing so, it allows for other modelling systems to be captured whose laws of interaction cannot be captured purely mechanistically, such as biological, economic and social systems, in contrast to those systems of a physical, chemical or epidemiological nature. Examples include agroecological, bioeconomic and Earth systems modelling, and the development of `psymple` is a necessary first step in the development and release of these tools.

# Description

The workings of `psymple` are based on the ideas of category-theoretic dynamic systems modelling package `AlgebraicJulia.jl` [@l-b-p-f:2024], in which modular ‘ported’ objects, called resource sharers, containing ordinary differential equations expose internal variable states at different ports. Ports are linked by wires which represent the sharing of state variables accross the dynamics equations of the system to create complex interacting dynamical systems. Mathematically, ported objects form algebras over the operad of undirected wiring diagrams, see [@l-b-p-f:2022]. 

In `psymple`, these ideas are extended to realise functions as ported objects, called functional ported objects (FPOs) alongside dynamic resource shares, which in `psymple` are called variable ported objects (VPOs) and whose ports are called variable ports. FPOs contain systems of multivariate functions, whose values are exposed at output ports, and whose arguments can read in information from other FPO outputs or VPO variable ports. The structure of input ports is also introduced to VPOs by allowing functions defining differential equations to read information from input ports in the same way as FPOs.

Arbitrary combinations of FPOs and VPOs can be combined in composite ported objects (CPOs) which introduce directed wires, capturing the partial substitution of functional information, and variable wires which implement the functionality of resource sharing. CPOs can themselves read and expose information from input, output and variable ports to create fully modular and arbitrarily complex hybrid systems of both functional and dynamic components whose nested hierarchy can reflect model structure. 

`psymple` implements a string-based authoring interface which enables no-code authoring from Python dictionary objects or `JSON` file formats. Inputs are internally processed using the Python symbolic mathematics package `sympy` [@meur:2017] to allow for automatic collection and simplification of equations, the elimination of errors from manually combining complex system equations, and clear inspection of a whole system or some of its parts with automatic outputs including \LaTeX format. 

# Research

The development of `psymple` emerged as part of a collaborative effort between [IDEMS International](https://www.idems.international/) and [CASAS Global](https://casasglobal.org/) to increase the uptake, accessibility and impact of the physiologically-based demographic modelling (PBDM) framework. The development of `psymple` is a neccesary first step to capture PBDM in sufficient generality to enable modular and flexible implementations of existing and new models into the framework to drive future research and social impact potential.

# Acknowledgements

The collaboration between IDEMS International and CASAS Global enabled by a grant from the McKnight Foundations [Global Collaboration for Resilient Food Systems](https://www.ccrp.org/), grant number $23-149$. The authors would like to thank Prof. Andrew Guitierrez of CASAS Global for his incredibly deep insights and many helpful conversations, and to the researchers of the [Topos Institute](https://topos.institute/) for their helpful comments and support in developing on their work.

# References