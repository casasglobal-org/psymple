from DiscretisedModel_v2 import *

### Simplified Fly model

FlyEggs = Age_Structured_Population("fly_eggs", "DDTM", [3, 47.2, 9.1, DegreeDays, False, False])
FlyLarvae = Age_Structured_Population("fly_larvae", "DDTM", [3, 190, 9.1, DegreeDays, False, False])

FlyEggsLarvae = Stage_Structured_Population("fly_eggs_larvae")

FlyEggsLarvae.add_stages([FlyEggs, FlyLarvae], [FlyEggs.first.flow_rate])

### Simplified Olive model

OliveBuds = Age_Structured_Population("olive_buds", "DDTM", [3, 390, 8.0, DegreeDays, False, False])
OliveFruit = Age_Structured_Population("olive_fruit", "DDTM", [3, 1500, 8.0, DegreeDays, False, False])

OliveBudsFruit = Stage_Structured_Population("olive_buds_fruit")

OliveBudsFruit.add_stages([OliveBuds, OliveFruit], [OliveBuds.first.flow_rate])

### Olive System

OliveSystem = Multi_Species_Population("olive_system")

OliveSystem.add_population(OliveBudsFruit)
OliveSystem.add_population(FlyEggsLarvae)

OliveSystem.add_interaction([FlyEggs, OliveFruit])

print([v.symbol for v in OliveSystem.variables])
print([e.equation for e in OliveSystem.expressions])
