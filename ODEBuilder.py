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


birds = Population('birds')
cats = Population('cats')

eggs = Subpopulation('eggs', birds)
chicks = Subpopulation('chicks', birds)

eggs.add_growth_rate(3)
eggs.add_capacity(5000)
cats.add_growth_rate(0)
chicks.add_growth_rate(0)

ODE = System()

ODE.add_population(birds)
ODE.add_population(cats)

sol = ODE.sol([0,25],[1,0,0])

print_sol(sol,[0,25])
 





'''


worms = Population('worms')
birds = Population('birds')
cats = Population('cats')

eggs = Subpopulation('eggs',birds)
chicks = Subpopulation('chicks',birds)
adults = Subpopulation('adults',birds)

print(worms.id,eggs.id,chicks.id)

worms.add_growth_rate(3)
eggs.add_growth_rate(-1)
#eggs.add_capacity(1000)
adults.add_growth_rate(-0.5)
chicks.add_growth_rate(0)
birds.link_lifestage(adults,eggs,1)
#birds.link_lifestage(adults,chicks,0)
#cats.add_growth_rate(-0.2)

ODE = System()

ODE.add_population(worms)
ODE.add_population(birds)
#ODE.add_population(cats)

ODE.add_interaction(worms,eggs,0,1/45)
ODE.add_interaction(worms,adults,-0.1,0)

print(ODE.get_ODEs_subbed(),ODE.constants)

sol = ODE.sol([0,10],[50,20,0,0])

print_sol(sol)



rats = Population('rats')
cats = Population('cats')

#baby_rats = Subpopulation('baby rats',rats)
#teen_rats = Subpopulation('teen rats',rats)
#adult_rats = Subpopulation('adult rats',rats)
#retired_rats = Subpopulation('retired rats',rats)

newborn_kittens = Subpopulation('newborn kittens',cats)
kittens = Subpopulation('kittens',cats)
adult_cats = Subpopulation('adult cats',cats)
senior_cats = Subpopulation('senior cats',cats)

newborn_kittens.add_growth_rate(5*sym.sin(T)+0.2)
newborn_kittens.add_capacity(5000)
senior_cats.add_growth_rate(-0.4)
cats.link_lifestage(kittens,newborn_kittens,1.5)
cats.link_lifestage(adult_cats,kittens,0.8)
cats.link_lifestage(senior_cats,adult_cats,0.5)

print([subpop.ODE for subpop in cats.subspecies])

ODE = System()

ODE.add_population(cats)

ODE_sol = ODE.sol([0,25],[1000,0,0,0])

print_sol(ODE_sol)




ODE = System()

ODE.add_population(rats)
ODE.add_population(cats)

ODE.add_interaction(rats,cats,-0.1,0.03)

#print(ODE.constants, rats.constants)

#print(ODE.get_names(),ODE.get_vars(),ODE.get_ODEs())

#print(ODE.populations,ODE.constants,ODE.vars)

ODE_sol1 = ODE.sol([0,25],[50,20])


print_sol(ODE_sol1)




'''