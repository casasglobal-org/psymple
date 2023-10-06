from ODEBuilder import *

k_OliveEgg = 10     ### Number of cohorts of Olive Fly Eggs
k_OliveAdult = 10     ### Number of cohorts of Olive Fly Adults

OliveEgg = [Unit(f"OliveEgg_{i}") for i in range(1,k_OliveEgg+1)]       ### Creates 10 cohorts of Olive Fly Eggs
OliveAdult = [Unit(f"OliveAdult_{i}") for i in range(1,k_OliveAdult+1)]

OliveEgg[0].update_initial_value(30)    ### Initial value of Olive Eggs (all other initial values are default 0)
OliveAdult[0].update_initial_value(10)
OliveEgg[0].add_growth_rate(-0.1)       ### Guess initial mortality of Eggs

### Create a population for Olive Eggs, add each cohort, and link the cohorts sequentially

OliveEggPopulation = Population('OliveEggs')   

for i in range(k_OliveEgg):
    OliveEggPopulation.add_unit(OliveEgg[i])
    if i > 0:
        OliveEggPopulation.link_lifestage(OliveEgg[i-1],OliveEgg[i],0.5)

### Create a population for Olive Flies, add each cohort, and link the cohorts sequentially

OliveAdultPopulation = Population('OliveAdults')

for i in range(k_OliveAdult):
    OliveAdultPopulation.add_unit(OliveAdult[i])
    if i > 0:
        OliveAdultPopulation.link_lifestage(OliveAdult[i-1],OliveAdult[i],0.1)

### Create an overarching population for Olive Flies (Eggs + Adults), and link the last cohort of eggs to the first cohort of adults

OliveFlyCycle = Population('OliveFlyCycle')

OliveFlyCycle.add_system(OliveEggPopulation)
OliveFlyCycle.add_system(OliveAdultPopulation)

OliveFlyCycle.link_lifestage(OliveEgg[-1],OliveAdult[0],0.1)

### Solve and print the system

OliveFlyCycle.sol([0,180],print = True)



