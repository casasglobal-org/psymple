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
 - name: 
    Agenzia nazionale per le nuove tecnologie, l’energia e lo sviluppo economico sostenibile (ENEA),
    Centro Ricerche Casaccia, Via Anguillarese 301, 00123 Rome, Italy
   index: 2
 - name: 
    Center for the Analysis of Sustainable Agricultural Systems, 37 Arlington Ave, Kensington,
    CA 94707-1035, USA
   index: 3
date: 04 September 2024
bibliography: paper.bib
---

# Summary

The modelling of complex systems, those systems characterised by high degrees of interdependence amongst components, is continually evolving in response to developing computing and visualisation power. Examples such as ecological, economic or social systems are classically modelled using statistical or correlative techniques, which have natural shortcomings when used for predictive modelling outside of the range of their parametrisation data.

Predictive modelling is improved by mechanistic models which deterministically capture the evolution of a system, or hybrid models consisting of mechanistic and correlative components. These models often feature significantly increased size and complexity, and there has been a growing requirement for so-called next generation modelling platforms which are built to a specification requiring modular and data-first implementations which drive clear, adaptable, reusable and accessible modelling practices.

The platform `psymple` is designed to facilitate the development of hybrid complex system models and modelling frameworks. It allows users to link together arbitrary combinations of modular mechanistic and functional components to build categorical diagrams representing a complex system. A compilation process automatically generates simulatable system equations from these diagrams using symbolic mathematics package `sympy`. Ultimately, this allows users to focus on the components and interactions of models, rather than their complex equation structure. 

# Statement of need

The development of `psymple` emerged from the complex system modelling requirements of ecological systems. Ecological niche models, also called species distribution models (SDMs) predict species distributions in response to environmental variables such as geographic and climatic features [@el-fr:2017; @el-le:2009]. Classically, these models are formed using correlative or statistical approaches which match observational data to a set of environmental variables to produce favourability ranges for each species.

An alternative approach to SDM is mechanistic modelling, which uses physiological species data to parametrise population dynamics models which respond to environmental inputs [@ke-po:2009]. Mechanistic SDMs decouple the physiology of a species from their native geography or climate, and allow species distribution models in new geographic or climatic regimes to be created in the absence of observational data [@john:2019].

In the more general context of complex systems modelling, the two schools of thought around using mechanistic or correlative approaches remain largely disjoint. The choice between them is normally made based on resource, expertise, or data constraints. More recently, the development of models sitting between the two extremes, using components and ideas from both mechanistic and correlative modelling, has been considered [@buck:2010; @to-va:2023]. These approaches are referred to as hybrid or spectrum modelling.

An example hybrid framework in ecological modelling is physiologically-based demographic modelling (PBDM), which uses physiological data to parametrise functions capturing biophysical or biochemical mechanisms, for example, the development, mortality and fecundity rates of a species in response to environmental variables, see [@po-gu:2023] for an overview and references. The PBDM approach highlights the considerable advantages of mechanistic SDMs, such as being able to consider the effects of tritrophic ecosystem interactions [@g-y-n-e:1999], or modelling the effects of climate change [@guti:2023], while retaining the comparable ease of parametrisation as status-quo correlative models. 

The barrier to produce widespread mechanistic or hybrid complex system models is often cited as the lack of available modelling frameworks [@bu-c-j:2018], the lack of flexibility in existing models [@buck:2010], or the lack of modelling platforms to implement existing ideas [@po-gu:2023]. The package `psymple` is a general platform designed to facilitate the creation of hybrid complex systems models and modelling frameworks. 

Models in `psymple` are built from arbitrary combinations of modular mechanistic, dynamic components and correlative, functional components which naturally interact with each other. This structure allows for the creation of modelling frameworks such as PBDM, and more widely those capturing biological, economic and social systems, for which capturing laws of interaction solely mechanistically is unfeasible. Examples include agroecological, bioeconomic and Earth systems modelling, and the development of `psymple` is a necessary first step in the development and release accessible and impactful tools in these areas. 

# Description

The workings of `psymple` are based on the ideas of category-theoretic dynamic systems modelling package `AlgebraicJulia.jl` [@l-b-p-f:2024], in which modular ‘ported’ objects, called resource sharers, containing ordinary differential equations expose internal variable states at different ports. Ports are linked by wires which represent the sharing of state variables across the dynamics equations of the system to create complex interacting dynamical systems. Mathematically, ported objects form algebras over the operad of undirected wiring diagrams, see [@l-b-p-f:2022]. 

In `psymple`, these ideas are extended to realise functions as ported objects, called functional ported objects (FPOs) alongside dynamic resource shares, which in `psymple` are called variable ported objects (VPOs) and whose ports are called variable ports. FPOs contain systems of multivariate functions, whose values are exposed at output ports, and whose arguments can read in information from other FPO outputs or VPO variable ports. The structure of input ports is also introduced to VPOs by allowing functions defining differential equations to read information from input ports in the same way as FPOs.

Arbitrary combinations of FPOs and VPOs can be combined in composite ported objects (CPOs) which introduce directed wires, capturing the partial substitution of functional information, and variable wires which implement the functionality of resource sharing. CPOs can themselves read and expose information from input, output and variable ports to create fully modular and arbitrarily complex hybrid systems of both functional and dynamic components whose nested hierarchy can reflect model structure. 

More generally, `psymple` is build to a specification shared by "next-generation" dynamical systems modelling frameworks, see [@baez:2023], including being *faceted*, where models can be considered one piece at a time; *modular*, where components naturally compose together; and *functorial*, where the data describing the system is separated from its functionality. These ideas allow for legible modelling of highly complex, specialised systems, and drive clear, adaptable and accessible modelling practices. For example, modular structures pave the way for cross-platform integrations and promote reuse and flexibility, while an abstracted data structure enables the creation of low- or no-code interfaces to improve utilisation amongst non-specialist users

Concretely, the faceted, modular structure provided by ported objects in `psymple` is complemented by a string-based authoring interface which enables no-code authoring from Python dictionary objects or `JSON` file formats. The data defining ported objects is internally processed through a composition process using the Python symbolic mathematics package `sympy` [@meur:2017]. This enables the automatic collection and simplification of equations, the elimination of errors from manually combining complex system equations, and clear inspection of a whole system, or its parts, with automatic outputs including \LaTeX format. 

# Research

The development of `psymple` emerged as part of a collaborative effort between [IDEMS International](https://www.idems.international/) and [CASAS Global](https://casasglobal.org/) to increase the uptake, accessibility and impact of the physiologically-based demographic modelling (PBDM) framework. The development of `psymple` is a necessary first step to capture PBDM in sufficient generality to enable modular and flexible implementations of existing and new models into the framework to drive future research and impact potential.

The specification of `psymple` was created in reference to the [collaborative modelling](https://topos.institute/collaborative-modelling) approach headed-up by the [Topos Institute](https://topos.institute/), which uses applied mathematical category theory to capture the mechanisms required to create modelling frameworks collaboratively, accounting for diversity in technical language, data availability and subject expertise.

This specification, coupled with the generality and flexibility of `psymple`, enables frameworks beyond PBDM to be developed or implemented and pushed towards new research and impacts. Research is currently active in bioeconomic modelling, see [@guti:2020; @r-g-s-z:1998] and ideas are being conceived around applications in Earth systems modelling, multi-layer modelling incorporating feedback loops to modelling techniques such as [collaborative agent-based modelling](https://johncarlosbaez.wordpress.com/2023/08/17/agent-based-models-part-2/), and data management and source control across collaborative practices.

# Acknowledgements

The collaboration between IDEMS International and CASAS Global is enabled by the McKnight Foundation's [Global Collaboration for Resilient Food Systems](https://www.ccrp.org/), grant number $23-149$. The authors would like to thank Prof. Andrew Gutierrez of CASAS Global for his incredibly deep insights and many helpful conversations, and to the researchers of the Topos Institute for their helpful comments and support in developing on their work.

# References