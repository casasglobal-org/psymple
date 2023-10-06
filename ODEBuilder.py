import sympy as sym
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import numpy as np

T = sym.Symbol('T')

class System:

    def __init__(self,name: str = ""):
        self.components = []
        self.vars = []
        self.params = {}
        self.systems = 0
        self.name = name
        self.ODEs_changed = True

    def add_system(self,system):
        self.components += system.components
        self.params = {**self.params,**system.params}
        self.systems += 1
        for comp in system.components:          
            if hasattr(comp,'id'):
                comp.id = f"{self.systems}_{comp.id}"
            else:
                comp.id = f"{self.systems}"

    def remove_system(self,system):
        pass

    def add_interaction(self,pop_1,pop_2,rate_12,rate_21):
        rate_12_symbol = sym.Symbol(f"c_[{pop_1.name} -> {pop_2.name}]")
        rate_21_symbol = sym.Symbol(f"c_[{pop_2.name} -> {pop_1.name}]")
        self.change_ODEs([pop_1,pop_2],[rate_12_symbol * pop_1.global_var_name * pop_2.global_var_name,rate_21_symbol * pop_1.global_var_name * pop_2.global_var_name])
        self.params.update({f"{pop_1.name} to {pop_2.name} rate": [rate_12_symbol, rate_12]})
        self.params.update({f"{pop_2.name} to {pop_1.name} rate": [rate_21_symbol, rate_21]})

    def change_ODEs(self,pops: list,updates: list):
        for pop, update in zip(pops,updates):
            pop.ODE += update
        self.ODEs_changed = True

    def assign_vars(self):
        self.vars = [comp.global_var_name for comp in self.components]

    def get_ODEs_subbed(self):
        self.all_params = [self.params[param] for param in self.params]
        return [pop.ODE.subs(self.all_params) for pop in self.components]       

    def get_initial_values(self):
        return [pop.initial_value for pop in self.components]

    def ODE_lambdify(self):
        ODE_system_subbed = self.get_ODEs_subbed() 
        self.assign_vars()
        self.ODE_system = [sym.lambdify([T,self.vars],ODE) for ODE in ODE_system_subbed]  ###self.vars is not what we want?
        self.ODEs_changed = False
       
    def ODE_constructor(self,t,y):
        if self.ODEs_changed == True:
            self.ODE_lambdify()
        return [f(t,y) for f in self.ODE_system] 

    def sol(self,t_range,print: bool = False):
        y0 = self.get_initial_values()
        solution = solve_ivp(self.ODE_constructor,t_range,y0,dense_output=True)
        if print == True:
            t = np.linspace(t_range[0],t_range[1],1001)
            plt.plot(t, solution.sol(t).T)
            plt.legend([self.components[i].name for i in range(len(self.components))], loc='best')
            plt.xlabel('t')
            plt.grid()
            plt.show()



class Population(System):

    def add_unit(self,unit):
        super().add_system(unit)

    def link_lifestage(self,pop_1,pop_2,rate_12):
        rate_12_symbol = sym.Symbol(f"k_[{pop_1.name} -> {pop_2.name}]")
        self.change_ODEs([pop_2],[rate_12_symbol*(pop_1.global_var_name - pop_2.global_var_name)])
        self.params.update({f"{pop_2.name} transfer rate": [rate_12_symbol,rate_12]})

    def add_summary():
        pass
        

class Unit(Population):

    def __init__(self,name: str,initial_value: float = 0):
        super().__init__(name)
        self.components.append(self)
        self.global_var_name = sym.Symbol(f"x_{name}")
        self.initial_value = initial_value
        self.ODE = 0

    def add_growth_rate(self,rate: float = 0):
        growth_rate_symbol = sym.Symbol(f"r_{self.name}")
        self.change_ODEs([self],[growth_rate_symbol * self.global_var_name])
        self.params.update({f"{self.name} growth rate": [growth_rate_symbol, rate]})

    def add_capacity(self,capacity: float = 0):
        capacity_symbol = sym.Symbol(f"K_{self.name}")
        growth_rate_symbol = self.params[f"{self.name} growth rate"][0]
        self.change_ODEs([self],[-self.global_var_name**2 * growth_rate_symbol / capacity_symbol])
        self.params.update({f"{self.name} capacity": [capacity_symbol, capacity]})


    def update_initial_value(self,initial_value: float = 0):
        self.initial_value = initial_value


