import unittest
from psymple.populations import Population
from psymple.custom_functions import DegreeDays


# Note: these classes are mostly for structuring tests.
# You can define as many as you want.
# You can also have multiple files starting with test_

# https://docs.python.org/3/library/unittest.html
class TestVariablesFromPopulation(unittest.TestCase):

    # Auxiliary function that doesn't start with test_
    def check_variables(self, population, expected):
        variables = population.variables.get_symbols()
        variable_names = [v.name for v in variables]
        self.assertEqual(set(variable_names), set(expected))

    # Each function starting with test_ is a test.
    def test_single_variable(self):
        flyeggs1 = Population("flyeggs1")
        self.check_variables(flyeggs1, ["x_flyeggs1"])

    def test_two_variables(self):
        flyeggs1 = Population("flyeggs1")
        flyeggs2 = Population("flyeggs2")
        flyeggs = Population("flyeggs")
        flyeggs._add_population(flyeggs1)
        flyeggs._add_population(flyeggs2)

        self.check_variables(flyeggs, ["x_flyeggs", "x_flyeggs1", "x_flyeggs2"])

class TestCustomFunctions(unittest.TestCase):
    def test_DegreeDays(self): 
        self.assertAlmostEqual(DegreeDays(6.0, 9.1), 3.9372650)
        self.assertEqual(DegreeDays(6.0, 23.2), 0)
        self.assertEqual(DegreeDays(6.0, 2.0), 9.575)
        self.assertEqual(DegreeDays(-1.0, 9.1), 0)
        
