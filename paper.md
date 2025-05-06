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
  - name: Andrew Paul Gutierrez
    orcid: 0000-0001-7773-1715
    affiliation: "3, 4"
  - name: Chiara Facciolà
    orcid: 0000-0001-8359-9300
    affiliation: 1
  - name: Timothy Hosgood
    orcid: 0000-0003-4580-0741
    affiliation: 5

affiliations:
 - name: IDEMS International CIC, United Kingdom
   index: 1
 - name: 
    Agenzia nazionale per le nuove tecnologie, l’energia e lo sviluppo economico sostenibile (ENEA), Italy
   index: 2
 - name: 
    Center for the Analysis of Sustainable Agricultural Systems (casasglobal.org), USA
   index: 3
 - name:
    Division of Ecosystem Science, College of Natural Resources, University of California, Berkeley, USA
   index: 4
 - name:
    Topos Institute, Berkeley, USA
   index: 5
date: 13 September 2024
bibliography: paper.bib
---

# Summary

The modelling of complex systems, which are characterised by high degrees of interdependence amongst components, is continually evolving in response to developing computing and visualisation power. Examples such as ecological, economic or social systems are classically modelled using statistical or correlative techniques, which have natural shortcomings when used for predictive modelling outside of the range of their parameterisation data.

Predictive modelling is improved by deterministic models which capture the evolution of a system, or by hybrid models composed of both deterministic and correlative parts. These models often feature significantly increased size and complexity, and there has been a growing requirement for so-called next generation modelling platforms which are built to a specification requiring modular and data-first implementations which drive clear, adaptable, reusable and accessible modelling practices.

The platform `psymple` is designed to facilitate the development of hybrid complex system models and modelling frameworks. It allows users to link together arbitrary combinations of modular differential equation systems and functional components to build categorical diagrams representing a complex system. A compilation process automatically generates simulatable system equations from these diagrams using the symbolic mathematics package `sympy`. Ultimately, this allows users to focus on the components and interactions of models, rather than their complex equation structure. 

# Background in ecological systems modelling

The development of `psymple` emerged from the complex system modelling requirements of ecological systems. Ecological niche models, also called species distribution models (SDMs) predict species distributions in response to environmental variables such as geographic and climatic features [@el-fr:2017; @el-le:2009]. Classically, these models are formed using correlative or statistical approaches which match observational data to a set of environmental variables to produce favourability ranges for each species.

An alternative approach is mechanistic modelling, which instead of observational data use physiological data to capture the underlying mechanisms which drive species distribution, such as energy balance, population dynamics or response to climate [@ke-po:2009]. In contrast to correlative approaches, mechanistic SDMs decouple the physiology of a species from their native geography or climate, and allow SDMs in new geographic or climatic regimes to be created in the absence of observational data [@john:2019]. 

An example mechanistic framework is physiologically-based demographic modelling (PBDM) [@guti:1996], which creates holistic ecosystem models based on the weather-driven biology of component species, allowing for predictive phenology, age- or mass-structured population dynamics, and geographic distribution assessments [@gu-po:2022a; @gu-po:2022b; @guti:2025a]. With this approach, PBDM can account for tritrophic ecosystem interactions [@g-y-n-e:1999], or model the effects of climate change [@guti:2023].

While correlative SDMs and mechanistic frameworks such as PBDM are today often regarded as conceptually distinct and largely unintegrated [@dorm:2012], their development can be traced back to early common roots [@fi-ni:1970; @guti:1974; @dw-go:1978]. A component of the PBDM framework is the use of physiological data to parametrise "biodemographic" functions capturing biophysical or biochemical mechanisms, such as the development, mortality and fecundity rates of a species in response to environmental variables [@po-gu:2023].

The use of biodemographic functions in PBDM combines the considerable holistic advantages of mechanistic SDMs, while retaining the comparable ease of parametrisation as status-quo correlative models. More widely, there has been growing interest and development of ecological models explicitly composed of both correlative and mechanistic components [@buck:2010; @to-va:2023], combining the benefits of both areas. In the wider context of complex systems modelling, the approach of building composite models out of different techniques is called hybrid, or spectrum, modelling.  

# Statement of need

Complex system models, including highly-developed hybrid frameworks such as PBDM, share the same barriers to widespread adoption and implementation. These barriers include the lack of available modelling frameworks [@bu-c-j:2018], the lack of flexibility in existing models [@buck:2010], or the lack of modelling platforms to implement existing ideas [@guti:2025b; @po-gu:2023]. The package `psymple` is a general platform designed to facilitate the creation of hybrid complex systems models and modelling frameworks. 

Models in `psymple` are built from arbitrary combinations of modular mechanistic, dynamic components and correlative, functional components which naturally interact with each other. This structure allows for the systematic implementation of modelling frameworks such as PBDM, and, more widely, those capturing biological, economic and social systems, for which it is not feasible to capture the laws of interaction purely mechanistically. Examples include agroecological and bioeconomic models [@guti:2020; @gu-re:2005; @r-g-s-z:1998], and Earth system models capturing the biogeochemical interactions between ecosystems, humanity, and the climate [@flat:2011]. The development of of `psymple` is a necessary first step in the development and release of accessible and impactful tools in these areas. 

# Description

The workings of `psymple` are based on the ideas of the dynamic systems modelling package `AlgebraicJulia.jl` [@l-b-p-f:2024], in which modular objects, called *resource sharers*, containing ordinary differential equations (ODEs), are linked by wires representing the sharing of state variables across the dynamics equations of the system. In mathematical applied category theory, the objects and wires form a formal diagram which can be interpreted as an algebra over the operad of undirected wiring diagrams [@l-b-p-f:2022]. A compilation process maps this diagram to a system of ODEs by adding the right-hand side of all states connected to the same wiring system. 

For example, a resource sharer $A$ containing the ODE $\frac{dx_i}{dt} = f \left( x_1,t \right)$, is connected to another resource sharer $B$ containing the ODE $\frac{dx_2}{dt} = g \left(x_2,t,i_1 \right)$, where $i_1$ is a constant, by a wire identifying the states $x_1$ an $x_2$. On compilation, the resulting system contains the ODE $\frac{dz}{dt} = f \left( z,t \right) + g \left( z,t,i_1 \right)$, where $z$ is a common renaming of $x_1$ and $x_2$.  

In `psymple`, these ideas are extended to realise multivariate functions as ported objects, called functional ported objects (FPOs), alongside resource sharers, which in `psymple` are called variable ported objects (VPOs). A second type of wiring, directed wiring, is introduced, which formally represents partial functional substitution. Directed wires can read both the state variables of VPOs and the output calculations of FPOs, and pass this information to inputs of other FPOs.

For example, consider a FPO $C$ containing the functional calculation $o_1 = h \left(x_1,t,i_2 \right)$ using a system state $x_1$ and external input $i_2$. Viewing $A$ and $B$ as VPOs, connecting directed wires from the state $x_1$ of $A$ to the input $x_1$ of $C$, and from the output $o_1$ of $C$ to the input $i_1$ of $B$ produces another formal diagram. Together with the variable connection between $A$ and $B$, this diagram is compiled by `psymple` to the single ODE

$$
\frac{dz}{dt} = f \left( z,t \right) +  \left( z,t, h \left(z, t, i_2 \right) \right)
$$

which can then be simulated. Underneath, the equation manipulation and substitution is handled by the Python symbolic mathematics package `sympy` [@meur:2017].

In `psymple`, arbitrary nesting of these base objects happens inside a third object type called a composite ported object (CPO), which stores the information of the wiring between its child objects. CPOs can also be nested to obtain a system hierarchy which represents the modelled structure. Details of how to build VPO, FPO and CPO objects and compile them to simulatable systems is extensively covered in the [package documentation](https://casasglobal-org.github.io/psymple).

With these structures, `psymple` satisfies a specification shared by "next-generation" dynamical systems modelling frameworks [@baez:2023], including being *faceted*, where models can be considered one piece at a time; *modular*, where components naturally compose together; and *functorial*, where the data describing the model (its syntax) is systematically and reliably transformed into system behaviour (its semantics). These ideas allow for legible modelling of highly complex, specialised systems, and drive clear, adaptable and accessible modelling practices in line with those promoted by the [Open Modeling Foundation](https://www.openmodelingfoundation.org/). 

# Related software

Many software solutions exist to capture climate-driven behaviour within parts of agricultural ecosystems. For example, sophisticated climate-sensitive physiological crop models can be produced using `APSIM` [@holz:2014] or `DSSAT` [@jone:2003]. These systems implement approaches which can be traced back to common roots in the Dutch school of modelling [@dw-go:1978], but are not demographic in construct. For insects, `ILCYM` [@spor:2009] enables the creation of climate-driven pest insect phenology models for distribution and risk assessments. 

The goal of `psymple` and its framework is not to stand apart from this existing software, but instead enable the creation of software which can link between existing tools: in this context to enable assessments across ecosystems, including the plant, herbivore and natural enemy trophic levels and their interactions. 

# Related research

The development of `psymple` emerged as part of a collaborative effort between [IDEMS International](https://www.idems.international/) and [CASAS Global](https://casasglobal.org/) to increase the uptake, accessibility and impact of the physiologically-based demographic modelling (PBDM) framework. The development of `psymple` is a necessary first step to capture PBDM in sufficient generality to enable modular and flexible implementations of existing and new models into the framework to drive future research and impact potential.

The specification of `psymple` was created from the "collaborative modelling" approach headed-up by the [Topos Institute](https://topos.institute/), which uses the mathematical field of applied category theory to capture the mechanisms required to create modelling frameworks collaboratively, accounting for diversity in technical language, data availability and subject expertise. This specification, coupled with the generality and flexibility of `psymple`, enables frameworks beyond PBDM to be developed or implemented, and pushed towards new research and subsequent impacts.

For example, research is currently active in bioeconomic modelling, which extends the supply-demand and mass-structured mechanisms of PBDM to understand the economic interaction that humans have with agroecological systems [@guti:2020; @r-g-s-z:1998]. More widely, ideas are being conceived around applications in Earth system modelling [@flat:2011], multi-layer modelling incorporating feedback loops to modelling techniques such as [collaborative agent-based modelling](https://johncarlosbaez.wordpress.com/2023/08/17/agent-based-models-part-2/), and data management techniques such as source control and versioning across collaborative practices.

# Acknowledgements

The collaboration between IDEMS International and CASAS Global is enabled by the McKnight Foundation's [Global Collaboration for Resilient Food Systems](https://www.ccrp.org/), grant numbers $22-341$, $23-149$, and $24-124$. The authors would like to thank the members of CASAS Global for their insights in developing the vision for a modern implementation of PBDM, and Brendan Fong and the rest of the Topos team in Berkeley for hosting a seminar that kick-started much of the shared vision of this work.

# References