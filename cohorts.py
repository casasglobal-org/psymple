from system import Population, Cohort

k_OliveEgg = 10     ### Number of cohorts of Olive Fly Eggs
k_OliveAdult = 10     ### Number of cohorts of Olive Fly Adults

### Create a population for Olive Eggs, add each cohort, and link the cohorts sequentially
OliveEgg = Cohort('OliveEgg', k_OliveEgg)
OliveEgg.first().set_initial_value(30)    ### Initial value of Olive Eggs (all other initial values are default 0)
OliveEgg.first().add_growth_rate(-0.1)       ### Guess initial mortality of Eggs
OliveEgg.link_units(0.5)

### Create a population for Olive Flies, add each cohort, and link the cohorts sequentially
OliveAdult = Cohort('OliveAdule', k_OliveAdult)
OliveAdult.link_units(0.1)
OliveAdult.first().set_initial_value(10)

### Create an overarching population for Olive Flies (Eggs + Adults), and link the last cohort of eggs to the first cohort of adults

OliveFlyCycle = Population('OliveFlyCycle')
OliveFlyCycle.add_system(OliveEgg)
OliveFlyCycle.add_system(OliveAdult)
OliveFlyCycle.link_lifestage(OliveEgg.last(), OliveAdult.first(), 0.1)

### Solve and print the system

sol = OliveFlyCycle.solve([0,180])
sol.plot()



