import unittest
import sympy as sym

from psymple.variables import Variable

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
)

from psymple.build.assignments import (
    FunctionalAssignment,
    DifferentialAssignment,
)

from psymple.build.compiled_ports import CompiledPort

from psymple.build.ported_objects import DependencyError

from psymple.build.ports import (
    InputPort,
    VariablePort,
)

"""
class TestInitialization(unittest.TestCase):



 

    def test_two_variables(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.1 * sym.Symbol("rabbits"))
        rabbit_growth = VariablePortedObject("rabbit growth", assignments=[assg])

        foxes = Variable("foxes", 50)
        assg = DifferentialAssignment(foxes, 0.04 * sym.Symbol("foxes"))
        fox_growth = VariablePortedObject("fox growth", assignments=[assg])

        rabbits = Variable("rabbits", 50)
        foxes = Variable("foxes", 50)
        assg1 = DifferentialAssignment(
            rabbits, -0.6 * sym.Symbol("foxes") * sym.Symbol("rabbits")
        )
        assg2 = DifferentialAssignment(
            foxes, 0.3 * sym.Symbol("foxes") * sym.Symbol("rabbits")
        )
        predation = VariablePortedObject("predation", assignments=[assg1, assg2])

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_children(rabbit_growth, fox_growth, predation)
        cpo_eco.add_variable_ports(VariablePort("rabbits"))
        cpo_eco.add_variable_ports(VariablePort("foxes"))
        cpo_eco.add_variable_wire(
            ["rabbit growth.rabbits", "predation.rabbits"], "rabbits"
        )
        cpo_eco.add_variable_wire(
            ["fox growth.foxes", "predation.foxes"], "foxes"
        )

        compiled = cpo_eco.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIn("foxes", compiled.variable_ports)
        fox_port = compiled.variable_ports["foxes"]
        self.assertIsInstance(rabbit_port, CompiledPort)
        self.assertIsInstance(fox_port, CompiledPort)
        self.assertEqual(
            rabbit_port.assignment.expression,
            0.1 * sym.Symbol("rabbits")
            - 0.6 * sym.Symbol("foxes") * sym.Symbol("rabbits"),
        )
        self.assertEqual(
            fox_port.assignment.expression,
            0.04 * sym.Symbol("foxes")
            + 0.3 * sym.Symbol("foxes") * sym.Symbol("rabbits"),
        )


    Test deprecated due to changes in nested input handling.
    def test_nested_input_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", assignments=[assg], create_input_ports=False)
        rabbit_growth.add_input_port(InputPort("r_growth"))

        cpo_l2 = CompositePortedObject("level2")
        cpo_l2.add_child(rabbit_growth)
        cpo_l2.add_variable_port(VariablePort("rabbits_level2"))
        cpo_l2.add_input_port(InputPort("r_growth_level2"))
        cpo_l2.add_variable_wire(
            ["rabbit growth.rabbits"], "rabbits_level2"
        )
        cpo_l2.add_directed_wire("r_growth_level2", ["rabbit growth.r_growth"])

        cpo_l3 = CompositePortedObject("r_growth_level3")
        cpo_l3.add_child(cpo_l2)
        cpo_l3.add_variable_port(VariablePort("rabbits_level3"))
        cpo_l3.add_input_port(InputPort("r_growth_level3"))
        cpo_l3.add_variable_wire(
            ["level2.rabbits_level2"], "rabbits_level3"
        )
        cpo_l3.add_directed_wire("r_growth_level3", ["level2.r_growth_level2"])

        compiled = cpo_l3.compile()
        # This removes the input port and creates an internal assignment instead
        compiled.set_input_parameters([ParameterAssignment("r_growth_level3", 0.25)])

        self.assertIn("rabbits_level3", compiled.variable_ports)
        assg = compiled.variable_ports["rabbits_level3"].assignment
        self.assertEqual(
            assg.expression,
            sym.Symbol("r_growth_level3") * sym.Symbol("rabbits_level3"),
        )
        self.assertIn("r_growth_level3", compiled.internal_parameter_assignments)
        assg = compiled.internal_parameter_assignments["r_growth_level3"]
        self.assertEqual(assg.symbol, sym.Symbol("r_growth_level3"))
        self.assertEqual(assg.expression, sym.sympify(0.25))
    """



"""
Tests deprecated due to changes in Simulation class.

class TestSimulation(unittest.TestCase):
    def test_no_params(self):
        rabbits = Variable("rabbits", 2)
        assg = DifferentialAssignment(rabbits, 1 * sym.Symbol("rabbits"))
        vpo_growth = VariablePortedObject("rabbit growth", assignments=[assg])

        system = System(vpo_growth)

        sim = Simulation(system)
        sim._compute_substitutions()

        integrator = DiscreteIntegrator(sim, 2, 1)
        integrator._advance_time_unit(1)
        integrator._advance_time_unit(1)
        self.assertEqual(len(sim.variables), 2)
        self.assertIn(sym.Symbol("rabbits"), sim.variables.keys())
        variable = system.variables["rabbits"]
        self.assertEqual(variable.symbol, sym.Symbol("rabbits"))
        self.assertEqual(variable.time_series, [2, 4, 8])

    def test_functions(self):
        fpo2 = FunctionalPortedObject("double")
        fpo2.add_input_port(InputPort("old"))
        fpo2.add_parameter_assignments(ParameterAssignment("new", "2*old"))

        fpo3 = FunctionalPortedObject("triple")
        fpo3.add_input_port(InputPort("old"))
        fpo3.add_parameter_assignments(ParameterAssignment("new", "3*old"))

        rabbits = Variable("rabbits", 1)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", assignments=[assg], create_input_ports=False)
        rabbit_growth.add_input_port(InputPort("r_growth"))

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_child(rabbit_growth)
        cpo_eco.add_child(fpo2)
        cpo_eco.add_child(fpo3)
        cpo_eco.add_input_port(InputPort("r_growth", default_value=1))
        cpo_eco.add_directed_wire("r_growth", "double.old")
        cpo_eco.add_directed_wire("double.new", "triple.old")
        cpo_eco.add_directed_wire("triple.new", "rabbit growth.r_growth")
        cpo_eco.add_variable_port(VariablePort("rabbits"))
        cpo_eco.add_variable_wire(["rabbit growth.rabbits"], "rabbits")

        system = System(cpo_eco)

        sim = Simulation(system)
        sim._compute_substitutions()

        integrator = DiscreteIntegrator(sim, 2, 1)
        integrator._advance_time_unit(1)
        integrator._advance_time_unit(1)
        self.assertEqual(len(system.variables), 2)
        self.assertIn(sym.Symbol("rabbits"), system.variables.keys())
        variable = system.variables["rabbits"]
        self.assertEqual(variable.symbol, sym.Symbol("rabbits"))
        self.assertEqual(variable.time_series, [1, 7, 49])

    # def test_time_dependent_params(self):
    #     pop = Population("pop", initial_value=1)
    #     pop._add_parameter("basic", "growth", "r", "T+1")
    #     pop._add_update_rule("x_pop", "r_growth * x_pop")
    #     system = System(pop)
    #     system._compute_substitutions()
    #     system._advance_time(1)
    #     system._advance_time(1)
    #     system._advance_time(1)
    #     self.assertEqual(len(system.variables), 1)
    #     variable = system.variables[0]
    #     self.assertEqual(variable.symbol, sym.Symbol("x_pop"))
    #     # We're computing factorials here:
    #     # Init:             x = 1
    #     # Step 1: T=0  r=1  x = x+r*x = 2
    #     # Step 2: T=1  r=2  x = x+r*x = 6
    #     # Step 3: T=2  r=3  x = x+r*x = 24
    #     self.assertEqual(variable.time_series, [1, 2, 6, 24])
"""
