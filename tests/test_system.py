import unittest
from models.populations import Population
from models.system import PopulationSystemError, System


class TestSystemParameterOrdering(unittest.TestCase):
    '''
    Tests to ensure that the computation order of Parameters
    within a system works correctly.

    Tests to ensure that Parameters, Variables etc are extracted
    correctly when building a System from a Population should be
    elsewhere.
    '''

    def compute_ordered_param_names(self, population):
        system = System(population)
        params = system._compute_parameter_update_order()
        return tuple(p.symbol.name for p in params)

    def check_parameter_order(self, population, expected):
        '''
        population: Population whose parameters to order and compare
        expected: a set of potential orderings of its parameters.
            Each ordering is a tuple of strings (symbol names)
        '''

        param_names = self.compute_ordered_param_names(population)
        self.assertIn(param_names, expected)

    def check_expected_error(self, population):
        with self.assertRaises(PopulationSystemError):
            param_names = self.compute_ordered_param_names(population)

    def test_minimal(self):
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", 45)
        self.check_parameter_order(pop, {("r_growth_rate",)})

    def test_minimal_with_system_time(self):
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", "5*T")
        self.check_parameter_order(pop, {("r_growth_rate",)})

    def test_minimal_with_variable_reference(self):
        pop = Population("pop")
        pop._add_parameter("composite", "growth_rate", "r", "5*x_pop")
        self.check_parameter_order(pop, {("r_growth_rate",)})

    def test_undefined_reference(self):
        # In the future, the Population may already be able to catch this case,
        # making this test redundant (i.e. a similar test should be for Population)
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", "r_something*5")
        self.check_expected_error(pop)

    def test_unordered(self):
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", 45)
        pop._add_parameter("basic", "something", "r", 5)
        self.check_parameter_order(
            pop, {
                ("r_growth_rate", "r_something"),
                ("r_something", "r_growth_rate"),
            }
        )

    def test_basic_dependency(self):
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", "r_something*5")
        pop._add_parameter("basic", "something", "r", 5)
        self.check_parameter_order(pop, {("r_something", "r_growth_rate")})

    def test_cyclic_dependency(self):
        pop = Population("pop")
        pop._add_parameter("basic", "growth_rate", "r", "r_something*5")
        pop._add_parameter("basic", "something", "r", "r_growth_rate+10")
        self.check_expected_error(pop)

    def test_multiple_aspects(self):
        pop = Population("pop")
        pop._add_parameter("basic", "3", "r", "r_1+T")
        pop._add_parameter("basic", "4", "r", "r_3+r_2")
        pop._add_parameter("composite", "2", "r", "r_1*x_pop")
        pop._add_parameter("basic", "1", "r", 45)
        self.check_parameter_order(
            pop, {
                ("r_1", "r_2", "r_3", "r_4"),
                ("r_1", "r_3", "r_2", "r_4"),
            }
        )
