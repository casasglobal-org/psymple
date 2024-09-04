---
title: 'Psymple: A Python package complex systems modelling'
authors:
  - name: George Simmons
    orcid: 0000-0002-9076-4973
    corresponding: true
    affiliation: 1
  - name: David Stern
    affiliation: 1
  - name: Georg Osang
    affiliation: 1
  - name: Luigi Ponti
    affiliation: 2
  - name: Chiara Facciola
    affiliation: 1

affiliations:
 - name: IDEMS International CIC, Reading, United Kingdom
   index: 1
 - name: ENEA, Italy
   index: 2
date: 04 September 2024
bibliography: paper.bib
---

# Summary

The modelling of complex systems, those systems characterised by high degrees of interdependence amongst components, is continually evolving in response to developing computing and visualisation power. Examples such as ecological, economic or social systems are classically modelled using statistical or correlative techniques, which have natural shortcomings when used for predictive modelling outside of the range of their parametrisation data.

Predictive modelling is improved by mechanistic models which deterministically capture the evolution of a system, or hybrid models consisting of mechanistic and correlative components. These models often feature significantly increased size and complexity, and there has been a growing requirement for so-called next generation modelling platforms which are built to a specification requiring modular and data-first implementations which drive clear, adaptable, reusable and accessible modelling practices.

The platform `psymple` is designed to facilitate the development of hybrid complex system models and modelling frameworks. It allows users to link together arbitrary combinations of modular mechanistic and functional components to build categorical diagrams representing a complex system. A compilation process automatically generates simulable system equations from these diagrams using symbolic mathematics package `sympy`. Ultimately, this allows users to focus on the components and interactions of models, rather than their complex equation structure. 

# Statement of need

The development of `psymple` emerged from the complex system modelling requirements of ecological systems. Ecological niche models, also called species distribution models (SDMs) are designed to predict the distribution in response to geographic and climatic features [Elith, 2017; Elith & Leathwick, 2009]. These models are classically formed using correlative approaches which match observational data to a set of environmental variables to produce favorability ranges for each species.

An alternative approach to SDM is known as mechanistic modelling, which uses physiological species data to parametrise population dynamics models which respond to environmental inputs [Kearney & Porter, 2009]. Mechanistic SDMs decouple the physiology of a species from their geographic and climatic environment, and allow species distribution models which respond to environmental change to be created in the absence of observational data [Johnston et al. 2019].

More generally, these approaches can be summarised as statistical or correlative, against mechanistic or dynamic approaches to complex systems modelling. Classically, the choice between these approaches is often decided based on resource or expertise constraints. More recently, the development of models which use components and ideas from both approaches has been considered [Tourinho & Vale, 2021]. Sitting between the two extremes, these approaches are referred to as hybrid or spectrum models.

An example in ecological modelling is physiologically-based demographic modeling (PBDM), which uses physiological data to parametrise functions capturing biophysical or biochemical mechanisms, for example, the development, mortality and fecundity rates of a species in response to environmental variables (see [Ponti & Gutierrez, 2023] for an overview and references).  The PBDM approach highlights the considerable advantages of mechanistic SDMs, such as being able to consider the effects of tritrophic ecosystem interactions [Gutierrez et al., 1999], while retaining the comparable ease of parametrisation as status-quo correlative models. 

The barrier to produce widespread mechanistic or hybrid complex system models is often cited as the lack of available frameworks [Buckley et al., 2023] or the lack of modelling platforms to implement these frameworks, as in the case of PBDM [Ponti & Gutierrez, 2023]. It is built to a specification shared by next-generation dynamical systems modelling frameworks [Libkind et al., 2022; Baez et al., 2022], including being open-source, modular and data-first to drive clear, adaptable and accessible modelling practices. 

These ideas allow for legibility of even highly complex, specialised systems, allow for low- or no-code interfaces to improve utilisation amongst non-specialist audiences. Modular structures pave the way for cross-platform integrations, and abstracts the data structure from modelling objects to promote reuse and adaptability. 

Psymple is a general modelling platform designed to facilitate the creation of hybrid complex systems models. Models are built from arbitrary combinations of modular mechanistic, dynamic components and correlative, functional components which naturally interact with each other. In doing so, it allows for other modelling systems to be captured whose laws of interaction cannot be captured purely mechanistically, such as biological, economic and social systems, in contrast to those systems of a physical, chemical or epidemiological nature. Examples include agroecological, bioeconomic and Earth systems modelling, and the development of psymple is a necessary first step in the development and release of these tools.

# Description

The workings of psymple are based on the collaborative modelling approach of the Topos Institute [Libkind et al., 2021], where modular ‘ported’ objects containing ordinary differential equations expose internal variable states at different ports. Ports are linked by wires which automatically collect the dynamics equations of state variables across the system to create complex interacting dynamical systems.

We extend these ideas to realise functions as ported objects, called functional ported objects (FPOs) alongside dynamic resource shares, which in psymple are referred to as variable ported objects (VPOs). Instances of the FunctionalPortedObject class contain:
Assignment instances, which store multivariate functions;
OutputPort instances, which expose the value of the function elsewhere in the system;
InputPort instances, which read in information from other FPO outputs or VPO state variables.

We introduce the structure of input ports to VPOs by allowing dynamic equations to read information from InputPort instances in the same way as FPOs. We align the structures of VPOs and FPOs by storing differential equations as Assignment instances and ports exposing variable states as VariablePort instances.

Arbitrary combinations of FPOs and VPOs can be combined in composite ported objects (CPOs) which introduce directed wires capturing the composition of functional information and variable wires which implement the functionality of resource sharing. CPOs can themselves read and expose information from input, output and variable ports to create fully modular and arbitrarily complex hybrid systems of both functional and dynamic components. 

Psymple implements a string-based authoring interface which allows for complete no-code authoring from JSON file formats. Inputs are internally processed using the symbolic mathematics package sympy to allow for automatic collection and simplification of equations, the elimination of mistakes from manually combining complex system equations, and clear inspection of a whole system or some of its parts with automatic outputs including in LaTeX format. 

# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References