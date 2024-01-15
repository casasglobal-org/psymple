import unittest
import sympy as sym

from psymple.abstract import DependencyError
from psymple.populations import Population
from psymple.variables import SimVariable, SimParameter, SimUpdateRule
from psymple.system import PopulationSystemError, System


class TestInitialization(unittest.TestCase):

    def test_minimal(self):
        pop = Population("pop", initial_value=23.5)
        system = System(pop)
        self.assertEqual(len(system.variables), 1)
        variable = system.variables[0]
        self.assertIsNotNone(variable.update_rule)
        self.assertIsInstance(variable.update_rule, SimUpdateRule)
        self.assertEqual(variable.update_rule.equation, sym.sympify("0"))

    def test_basic(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_parameter("basic", "growth", "r", 0.1)
        pop._add_update_rule("x_pop", "r_growth * x_pop")
        system = System(pop)
        self.assertEqual(len(system.variables), 1)
        self.assertEqual(len(system.parameters), 1)
        variable = system.variables[0]
        self.assertIsInstance(variable, SimVariable)
        self.assertEqual(variable.symbol, sym.Symbol("x_pop"))
        self.assertEqual(variable.initial_value, 23.5)
        v_rule = variable.update_rule
        self.assertEqual(v_rule.equation, sym.sympify("r_growth * x_pop"))
        self.assertEqual(len(v_rule.variables), 1)
        self.assertEqual(len(v_rule.parameters), 1)
        self.assertEqual(v_rule.variables[0].symbol, sym.Symbol("x_pop"))
        self.assertEqual(v_rule.parameters[0].symbol, sym.Symbol("r_growth"))
        parameter = system.parameters[0]
        self.assertIsInstance(parameter, SimParameter)
        self.assertEqual(parameter.symbol, sym.Symbol("r_growth"))
        p_rule = parameter.update_rule
        self.assertIsNotNone(p_rule)
        self.assertIsInstance(p_rule, SimUpdateRule)
        self.assertEqual(p_rule.equation, sym.sympify("0.1"))
        self.assertEqual(len(p_rule.variables), 0)
        self.assertEqual(len(p_rule.parameters), 0)

    def test_update_rule_merge(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_parameter("basic", "growth", "r", 0.1)
        pop._add_update_rule("x_pop", "r_growth * x_pop")
        pop._add_update_rule("x_pop", 0.5)
        system = System(pop)
        self.assertEqual(len(system.variables), 1)
        v_rule = system.variables[0].update_rule
        self.assertEqual(v_rule.equation, sym.sympify("r_growth * x_pop + 0.5"))

    def test_time_dependent_parameter(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_parameter("basic", "growth", "r", "x_pop * T")
        system = System(pop)
        self.assertEqual(len(system.parameters), 1)
        p_rule = system.parameters[0].update_rule
        self.assertEqual(p_rule.equation, sym.sympify("x_pop * T"))
        self.assertEqual(len(p_rule.variables), 2)
        dependent_variables = p_rule.get_variables()
        self.assertIn(sym.Symbol("T"), dependent_variables)
        self.assertIn(sym.Symbol("x_pop"), dependent_variables)

    def test_time_dependent_variable(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_update_rule("x_pop", "T * 0.1")
        system = System(pop)
        self.assertEqual(len(system.variables), 1)
        v_rule = system.variables[0].update_rule
        self.assertEqual(len(v_rule.parameters), 0)
        self.assertEqual(len(v_rule.variables), 1)
        self.assertEqual(v_rule.variables[0].symbol, sym.Symbol("T"))


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

    def check_expected_error(self, population, error):
        with self.assertRaises(error):
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
        self.check_expected_error(pop, DependencyError)

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
        self.check_expected_error(pop, PopulationSystemError)

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


class TestParameterSubstitution(unittest.TestCase):

    def test_minimal_variable(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_parameter("basic", "growth", "r", 0.1)
        pop._add_update_rule("x_pop", "r_growth * x_pop")
        system = System(pop)
        system._compute_substitutions()
        self.assertEqual(len(system.variables), 1)
        self.assertEqual(len(system.parameters), 1)
        v_rule = system.variables[0].update_rule
        self.assertEqual(v_rule.equation, sym.sympify("0.1 * x_pop"))
        self.assertEqual(len(v_rule.variables), 1)
        self.assertEqual(len(v_rule.parameters), 0)
        self.assertEqual(v_rule.variables[0].symbol, sym.Symbol("x_pop"))

    def test_parameter_chain(self):
        pop = Population("pop", initial_value=23.5)
        pop._add_parameter("basic", "growth", "r", 0.1)
        pop._add_parameter("basic", "growth", "t", "(r_growth + 1) * T")
        pop._add_update_rule("x_pop", "r_growth * x_pop + t_growth")
        system = System(pop)
        system._compute_substitutions()
        self.assertEqual(len(system.variables), 1)
        self.assertEqual(len(system.parameters), 2)
        p0_rule = system.parameters[0].update_rule
        self.assertEqual(p0_rule.equation, sym.sympify("0.1"))
        p1_rule = system.parameters[1].update_rule
        self.assertEqual(p1_rule.equation, sym.sympify("1.1 * T"))
        self.assertEqual(len(p1_rule.variables), 1)
        self.assertEqual(len(p1_rule.parameters), 0)
        v_rule = system.variables[0].update_rule
        self.assertEqual(v_rule.equation, sym.sympify("0.1 * x_pop + 1.1 * T"))


class TestSimulation(unittest.TestCase):

    def test_time_advance(self):
        pop = Population("pop", initial_value=23.5)
        system = System(pop)
        system._advance_time(0.1)
        self.assertEqual(system.time.time_series, [0, 0.1])
        system._advance_time(0.1)
        self.assertEqual(system.time.time_series, [0, 0.1, 0.2])

    def test_no_params(self):
        pop = Population("pop", initial_value=2)
        pop._add_update_rule("x_pop", "1 * x_pop")
        system = System(pop)
        system._advance_time(1)
        system._advance_time(1)
        self.assertEqual(len(system.variables), 1)
        variable = system.variables[0]
        self.assertEqual(variable.symbol, sym.Symbol("x_pop"))
        self.assertEqual(variable.time_series, [2, 4, 8])

    def test_time_dependent_params(self):
        pop = Population("pop", initial_value=1)
        pop._add_parameter("basic", "growth", "r", "T+1")
        pop._add_update_rule("x_pop", "r_growth * x_pop")
        system = System(pop)
        system._compute_substitutions()
        system._advance_time(1)
        system._advance_time(1)
        system._advance_time(1)
        self.assertEqual(len(system.variables), 1)
        variable = system.variables[0]
        self.assertEqual(variable.symbol, sym.Symbol("x_pop"))
        # We're computing factorials here:
        # Init:             x = 1
        # Step 1: T=0  r=1  x = x+r*x = 2
        # Step 2: T=1  r=2  x = x+r*x = 6
        # Step 3: T=2  r=3  x = x+r*x = 24
        self.assertEqual(variable.time_series, [1, 2, 6, 24])
