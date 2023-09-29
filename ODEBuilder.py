import sympy as sym
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import numpy as np

T = sym.Symbol('T')

def print_sol(sol,t_range):
    t = np.linspace(t_range[0],t_range[1],1001)
    plt.plot(t, sol.sol(t).T)
    plt.legend(['pop1','pop2'], loc='best')
    plt.xlabel('t')
    plt.grid()
    plt.show()


class System:
    
    def __init__(self):
        self.populations = []
        self.params = {}
        self.vars = []
        self.ODEs_changed = True    ##tracks if time-intensive ODE_lambdify() should be called in ODE_constructor(). 
                                    ##Updated to True whenever there's a change to the system, and False when ODE_lambdify() is run.
                                    ##Better way to do this?

    def add_population(self,pop):
        pops_to_add = []
        if pop.subspecies == []:
            pops_to_add += [pop]
        else:
            pops_to_add += [subpop for subpop in pop.subspecies]
        self.init_population(pops_to_add)

    def init_population(self,pops):
        for pop in pops:
            self.populations.append(pop)
            self.params = {**self.params,**pop.params}
            self.vars.append(pop.var)
            self.all_params = [self.params[param] for param in self.params]
            self.ODEs_changed = True

    def get_names(self):
        return [self.populations[i].name for i in range(len(self.populations))]
    
    def get_vars(self):
        return [self.populations[i].var for i in range(len(self.populations))]
    
    def get_ODEs(self):
        return [self.populations[i].ODE for i in range(len(self.populations))]
    
    def get_ODEs_subbed(self):
        return [pop.ODE.subs(self.all_params) for pop in self.populations] 
    
    def add_interaction(self,pop_1,pop_2,rate_12 = 0,rate_21 = 0):
        rate_12_symbol = sym.Symbol(f"c[{pop_1.id}->{pop_2.id}]")
        rate_21_symbol = sym.Symbol(f"c[{pop_2.id}->{pop_1.id}]")
        self.params.update({f"{pop_1.name} on {pop_2.name} rate": [rate_12_symbol, rate_12]})
        self.params.update({f"{pop_2.name} on {pop_1.name} rate": [rate_21_symbol, rate_21]})
        pop_1.ODE += rate_12_symbol * pop_1.var * pop_2.var
        pop_2.ODE += rate_21_symbol * pop_2.var * pop_1.var
        self.ODEs_changed = True
    
    def ODE_lambdify(self):
        ODE_system_subbed = self.get_ODEs_subbed() 
        self.ODE_system = [sym.lambdify([T,self.vars],ODE) for ODE in ODE_system_subbed]
        self.ODEs_changed = False
       
    def ODE_constructor(self,t,y):
        if self.ODEs_changed == True:
            self.ODE_lambdify()
        return [f(t,y) for f in self.ODE_system] 

    def get_parameter_values(self):
        return [self.params[rate][1] for rate in self.params]
    
    def update_parameter(self,parameter,value):
        self.params[parameter][1] = value
    
    def sol(self,t_range,y0):
        return solve_ivp(self.ODE_constructor,t_range,y0,dense_output=True)

class Population:
    id = 1
    def __init__(self,name: str):
        self.id = Population.id
        Population.id += 1
        self.init_identifiers(name,self.id)

    def init_identifiers(self,name,id):
        self.name = name
        self.var = sym.Symbol(f"x_{id}")
        self.params = {}
        self.ODE = 0
        self.subspecies = []

    def add_growth_rate(self,rate = 0):
        growth_rate_symbol = sym.Symbol(f"r{self.id}")
        self.params.update({f"{self.name} growth rate": [growth_rate_symbol, rate]})
        self.ODE += growth_rate_symbol * self.var

    def add_capacity(self,capacity = 0):
        capacity_symbol = sym.Symbol(f"K{self.id}")
        self.params.update({f"{self.name} capacity": [capacity_symbol,capacity]})
        self.ODE += -self.params[f"{self.name} growth rate"][0] * self.var**2 / capacity_symbol
    
    def link_lifestage(self,lifestage,prev_lifestage,rate = 0):
        link_symbol = sym.Symbol(f"k{self.id}({prev_lifestage.id}->{lifestage.id})")
        lifestage.params.update({f"{prev_lifestage.name} to {lifestage.name} rate": [link_symbol,rate]})
        lifestage.ODE += link_symbol * (prev_lifestage.var - lifestage.var)

class Subpopulation(Population):
    def __init__(self,name: str,parent_species: Population):
        self.parent_species = parent_species
        parent_species.subspecies.append(self)
        self.id =  f"{parent_species.id}({len(parent_species.subspecies)})"
        super().init_identifiers(name,self.id)