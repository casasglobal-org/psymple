import unittest
import sympy as sym

# from psymple.populations import Population
# from psymple.variables import SimVariable, SimParameter, SimUpdateRule
from psymple.abstract import DependencyError
from psymple.variables import Variable

from psymple.system import PopulationSystemError, System
from psymple.ported_objects import (
    CompiledPort,
    CompiledInputPort,
    CompiledOutputPort,
    CompiledVariablePort,
    CompiledPortedObject,
    CompositePortedObject,
    DifferentialAssignment,
    DirectedWire,
    FunctionalPortedObject,
    InputPort,
    OutputPort,
    ParameterAssignment,
    Port,
    PortedObject,
    VariableAggregationWiring,
    VariablePort,
    VariablePortedObject,
    WiringError,
)


class TestInitialization(unittest.TestCase):
    def test_functional(self):
        fpo = FunctionalPortedObject(
            "double", [InputPort("old")], [ParameterAssignment("new", "2*old")]
        )

        # Test prefixing of symbols with PO name
        compiled = fpo.compile(prefix_names=True)
        self.assertEqual(len(compiled.output_ports), 1)
        self.assertEqual(len(compiled.input_ports), 1)
        in_port = compiled.input_ports["old"]
        out_port = compiled.output_ports["new"]
        self.assertEqual(in_port.name, "double.old")
        self.assertEqual(out_port.name, "double.new")
        self.assertEqual(out_port.assignment.expression, 2 * sym.Symbol("double.old"))

        # No prefixing
        compiled = fpo.compile()
        self.assertEqual(len(compiled.output_ports), 1)
        self.assertEqual(len(compiled.input_ports), 1)
        in_port = compiled.input_ports["old"]
        out_port = compiled.output_ports["new"]
        self.assertEqual(in_port.name, "old")
        self.assertEqual(out_port.name, "new")
        self.assertEqual(out_port.assignment.expression, 2 * sym.Symbol("old"))

    def test_functional2x2(self):
        fpo = FunctionalPortedObject(
            "operations",
            [InputPort("in1"), InputPort("in2")],
            [
                ParameterAssignment("sum", "in1+in2"),
                ParameterAssignment("prod", "in1*in2"),
            ],
        )
        compiled = fpo.compile()
        self.assertEqual(len(compiled.output_ports), 2)
        self.assertEqual(len(compiled.input_ports), 2)
        input_symbols = {port.name for port in compiled.input_ports.values()}
        self.assertEqual(input_symbols, {"in1", "in2"})
        output_symbols = {port.name for port in compiled.output_ports.values()}
        self.assertEqual(output_symbols, {"sum", "prod"})

    def test_variable_only(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.1 * sym.Symbol("rabbits"))
        vpo_growth = VariablePortedObject("rabbit growth", [assg])

        compiled = vpo_growth.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIsInstance(rabbit_port, CompiledPort)
        self.assertEqual(rabbit_port.assignment.expression, 0.1 * sym.Symbol("rabbits"))

    def test_unexposed_variable(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.1 * sym.Symbol("rabbits"))
        vpo_growth = VariablePortedObject("rabbit growth", [assg], expose_ports=False)

        compiled = vpo_growth.compile()
        self.assertIn("rabbits", compiled.internal_variable_assignments)
        assg = compiled.internal_variable_assignments["rabbits"]
        self.assertEqual(assg.expression, 0.1 * sym.Symbol("rabbits"))

    def test_variable_with_input(self):
        # To test: validation that all free parameters are inputs.
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])

        # r_growth has no corresponding input port yet
        with self.assertRaises(DependencyError):
            compiled = rabbit_growth.compile()

        rabbit_growth.add_input_port(InputPort("r_growth", default_value=0.01))

        compiled = rabbit_growth.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIsInstance(rabbit_port, CompiledPort)
        self.assertEqual(
            rabbit_port.assignment.expression,
            sym.Symbol("r_growth") * sym.Symbol("rabbits"),
        )

    def test_variable_composition(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, 0.1 * sym.Symbol("rabbits")
        )  # 0.1 is the growth rate
        vpo_growth = VariablePortedObject("rabbit growth", [assg])

        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, -0.05 * sym.Symbol("rabbits")
        )  # 0.05 is the death rate
        vpo_death = VariablePortedObject("rabbit death", [assg])

        cpo_rabbits = CompositePortedObject("rabbit system")
        cpo_rabbits.add_child(vpo_growth)
        cpo_rabbits.add_child(vpo_death)
        cpo_rabbits.add_variable_port(VariablePort("rabbits"))
        cpo_rabbits.add_variable_aggregation_wiring(
            ["rabbit growth.rabbits", "rabbit death.rabbits"], "rabbits"
        )

        compiled = cpo_rabbits.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIsInstance(rabbit_port, CompiledPort)
        self.assertEqual(
            rabbit_port.assignment.expression, 0.05 * sym.Symbol("rabbits")
        )

    def test_unexposed_renamed_variable_composition(self):
        inn = Variable("in", 25)
        out = Variable("out", 50)
        assg2 = DifferentialAssignment(
            inn, -0.1 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        assg1 = DifferentialAssignment(
            out, 0.1 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        vpo_1 = VariablePortedObject("flow1", [assg1, assg2])

        inn = Variable("in", 50)
        out = Variable("out", 75)
        assg2 = DifferentialAssignment(
            inn, -0.2 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        assg1 = DifferentialAssignment(
            out, 0.2 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        vpo_2 = VariablePortedObject("flow2", [assg1, assg2])

        cpo = CompositePortedObject("flow system")
        cpo.add_child(vpo_1)
        cpo.add_child(vpo_2)
        # unexposed flow transition variable
        cpo.add_variable_aggregation_wiring(
            ["flow1.out", "flow2.in"], output_name="mass"
        )
        # Exposed inflow variable
        cpo.add_variable_port(VariablePort("inflow"))
        cpo.add_variable_aggregation_wiring(["flow1.in"], "inflow")

        compiled = cpo.compile()

        self.assertIn("inflow", compiled.variable_ports)
        inflow_port = compiled.variable_ports["inflow"]
        self.assertIn("mass", compiled.internal_variable_assignments)
        mass_assg = compiled.internal_variable_assignments["mass"]
        self.assertIn("flow2.out", compiled.internal_variable_assignments)
        out_assg = compiled.internal_variable_assignments["flow2.out"]
        self.assertEqual(inflow_port.symbol, sym.Symbol("inflow"))
        self.assertEqual(
            inflow_port.assignment.expression,
            -0.1 * sym.Symbol("inflow"),
        )
        self.assertEqual(mass_assg.symbol, sym.Symbol("mass"))
        self.assertEqual(
            mass_assg.expression,
            0.1 * sym.Symbol("inflow") - 0.2 * sym.Symbol("mass"),
        )
        self.assertEqual(out_assg.symbol, sym.Symbol("flow2.out"))
        self.assertEqual(
            out_assg.expression,
            0.2 * sym.Symbol("mass"),
        )

    def test_two_variables(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.1 * sym.Symbol("rabbits"))
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])

        foxes = Variable("foxes", 50)
        assg = DifferentialAssignment(foxes, 0.04 * sym.Symbol("foxes"))
        fox_growth = VariablePortedObject("fox growth", [assg])

        rabbits = Variable("rabbits", 50)
        foxes = Variable("foxes", 50)
        assg1 = DifferentialAssignment(
            rabbits, -0.6 * sym.Symbol("foxes") * sym.Symbol("rabbits")
        )
        assg2 = DifferentialAssignment(
            foxes, 0.3 * sym.Symbol("foxes") * sym.Symbol("rabbits")
        )
        predation = VariablePortedObject("predation", [assg1, assg2])

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_child(rabbit_growth)
        cpo_eco.add_child(fox_growth)
        cpo_eco.add_child(predation)
        cpo_eco.add_variable_port(VariablePort("rabbits"))
        cpo_eco.add_variable_port(VariablePort("foxes"))
        cpo_eco.add_variable_aggregation_wiring(
            ["rabbit growth.rabbits", "predation.rabbits"], "rabbits"
        )
        cpo_eco.add_variable_aggregation_wiring(
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

    def test_input_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])
        growth_input_port = InputPort("r_growth", default_value=0.01)
        rabbit_growth.add_input_port(growth_input_port)

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_child(rabbit_growth)
        cpo_eco.add_variable_port(VariablePort("rabbits"))
        cpo_eco.add_variable_aggregation_wiring(["rabbit growth.rabbits"], "rabbits")

        # The r_growth child port is not connected, but has a default value
        compiled = cpo_eco.compile()
        self.assertEqual(len(compiled.internal_parameter_assignments), 1)
        self.assertIn("rabbit growth.r_growth", compiled.internal_parameter_assignments)
        param_assg = compiled.internal_parameter_assignments["rabbit growth.r_growth"]
        self.assertEqual(param_assg.name, "rabbit growth.r_growth")
        self.assertEqual(param_assg.expression, sym.sympify(0.01))

        self.assertEqual(len(compiled.variable_ports), 1)
        self.assertIn("rabbits", compiled.variable_ports)
        variable_port = compiled.variable_ports["rabbits"]
        self.assertEqual(variable_port.name, "rabbits")
        self.assertEqual(
            variable_port.assignment.expression,
            sym.Symbol("rabbit growth.r_growth") * sym.Symbol("rabbits"),
        )

        # We have an input port without default value and no incoming connection
        growth_input_port.default_value = None
        with self.assertRaises(WiringError):
            compiled = cpo_eco.compile()

        # The r_growth child port is now connected from the outside
        cpo_eco.add_input_port(InputPort("r_growth"))
        cpo_eco.add_directed_wire("r_growth", "rabbit growth.r_growth")
        compiled = cpo_eco.compile()

        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIsInstance(rabbit_port, CompiledVariablePort)
        self.assertEqual(rabbit_port.assignment.name, "rabbits")
        # The input parameter name has been subbed into the expression below
        self.assertEqual(
            rabbit_port.assignment.expression,
            sym.Symbol("r_growth") * sym.Symbol("rabbits"),
        )
        self.assertIn("r_growth", compiled.input_ports)
        growth_port = compiled.input_ports["r_growth"]
        self.assertIsInstance(growth_port, CompiledInputPort)
        self.assertEqual(growth_port.name, "r_growth")

    def test_nested_input_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])
        rabbit_growth.add_input_port(InputPort("r_growth"))

        cpo_l2 = CompositePortedObject("level2")
        cpo_l2.add_child(rabbit_growth)
        cpo_l2.add_variable_port(VariablePort("rabbits_level2"))
        cpo_l2.add_input_port(InputPort("r_growth_level2"))
        cpo_l2.add_variable_aggregation_wiring(
            ["rabbit growth.rabbits"], "rabbits_level2"
        )
        cpo_l2.add_directed_wire("r_growth_level2", "rabbit growth.r_growth")

        cpo_l3 = CompositePortedObject("r_growth_level3")
        cpo_l3.add_child(cpo_l2)
        cpo_l3.add_variable_port(VariablePort("rabbits_level3"))
        cpo_l3.add_input_port(InputPort("r_growth_level3"))
        cpo_l3.add_variable_aggregation_wiring(
            ["level2.rabbits_level2"], "rabbits_level3"
        )
        cpo_l3.add_directed_wire("r_growth_level3", "level2.r_growth_level2")

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

    def test_output_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.01 * sym.Symbol("rabbits"))
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])

        fpo = FunctionalPortedObject("double")
        fpo.add_assignment(ParameterAssignment("new", "2*old"), create_input_ports=True)

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_child(rabbit_growth)
        cpo_eco.add_child(fpo)
        cpo_eco.add_variable_port(VariablePort("rabbits"))
        cpo_eco.add_output_port(OutputPort("doublerab"))
        cpo_eco.add_variable_aggregation_wiring(["rabbit growth.rabbits"], "rabbits")
        cpo_eco.add_directed_wire("rabbit growth.rabbits", "double.old")
        cpo_eco.add_directed_wire("double.new", "doublerab")

        compiled = cpo_eco.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIn("doublerab", compiled.output_ports)
        doublerab_port = compiled.output_ports["doublerab"]
        self.assertIn("double.new", compiled.internal_parameter_assignments)
        double_assg = compiled.internal_parameter_assignments["double.new"]
        self.assertEqual(rabbit_port.symbol, sym.Symbol("rabbits"))
        self.assertEqual(doublerab_port.symbol, sym.Symbol("doublerab"))
        self.assertEqual(
            doublerab_port.assignment.expression,
            sym.Symbol("double.new"),
        )
        self.assertEqual(double_assg.symbol, sym.Symbol("double.new"))
        self.assertEqual(
            double_assg.expression,
            2 * sym.Symbol("rabbits"),
        )

    def test_output_nesting(self):
        # TODO: Add checks
        A_func = FunctionalPortedObject("func")
        A_func.add_input_port(InputPort("X", default_value = 5))
        A_func.add_assignment(ParameterAssignment("Y", "X"))

        A = CompositePortedObject("A")
        A.add_child(A_func)
        A.add_output_port(OutputPort("Y"))
        A.add_directed_wire("func.Y", "Y")

        B = CompositePortedObject("B")
        B.add_output_port(OutputPort("BY"))
        B.add_child(A)
        B.add_directed_wire("A.Y", "BY")

        compiled = B.compile()

    def test_parameters(self):
        fpo = FunctionalPortedObject("double")
        fpo.add_input_port(InputPort("old"))
        fpo.add_assignment(ParameterAssignment("new", "2*old"))

        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])
        rabbit_growth.add_input_port(InputPort("r_growth"))

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_child(rabbit_growth)
        cpo_eco.add_child(fpo)
        cpo_eco.add_input_port(InputPort("r_growth", default_value=0.01))
        cpo_eco.add_directed_wire("r_growth", "double.old")
        cpo_eco.add_directed_wire("double.new", "rabbit growth.r_growth")
        cpo_eco.add_variable_port(VariablePort("rabbits"))
        cpo_eco.add_variable_aggregation_wiring(["rabbit growth.rabbits"], "rabbits")

        compiled = cpo_eco.compile()
        self.assertIn("r_growth", compiled.input_ports)
        growth_port = compiled.input_ports["r_growth"]
        self.assertEqual(growth_port.name, "r_growth")

        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertEqual(rabbit_port.assignment.name, "rabbits")

        # This is how it currently works, but future implementation
        # May substitute double.new away as well.
        self.assertIn("double.new", compiled.internal_parameter_assignments)
        double_assg = compiled.internal_parameter_assignments["double.new"]
        self.assertEqual(double_assg.name, "double.new")
        self.assertEqual(
            rabbit_port.assignment.expression,
            sym.Symbol("double.new") * sym.Symbol("rabbits"),
        )

    def test_key_remapping(self):
        # TODO: Add checks
        func_1 = FunctionalPortedObject("func_1")
        func_1.add_input_port(InputPort("X", default_value = 5))
        func_1.add_assignment(ParameterAssignment("Y", "X"))

        A = CompositePortedObject("A")
        A.add_child(func_1)
        A.add_input_port(InputPort("X", default_value = 3))
        A.add_output_port(OutputPort("Y"))
        A.add_directed_wire("X", "func_1.X")
        A.add_directed_wire("func_1.Y", "Y")

        B = CompositePortedObject("B")
        B.add_child(A)
        B.add_input_port(InputPort("X", default_value = 1))
        B.add_output_port(OutputPort("Y"))
        B.add_directed_wire("X", "A.X")
        B.add_directed_wire("A.Y", "Y")

        C = CompositePortedObject("C")
        C.add_child(B)

        compiled = C.compile()

class TestSimulation(unittest.TestCase):
    def test_no_params(self):
        rabbits = Variable("rabbits", 2)
        assg = DifferentialAssignment(rabbits, 1 * sym.Symbol("rabbits"))
        vpo_growth = VariablePortedObject("rabbit growth", [assg])
        compiled = vpo_growth.compile()

        var, par = compiled.get_assignments()
        system = System(variable_assignments=var, parameter_assignments=par)

        system._compute_substitutions()
        system._advance_time(1)
        system._advance_time(1)
        self.assertEqual(len(system.variables), 1)
        variable = system.variables[0]
        self.assertEqual(variable.symbol, sym.Symbol("rabbits"))
        self.assertEqual(variable.time_series, [2, 4, 8])

    def test_functions(self):
        fpo2 = FunctionalPortedObject("double")
        fpo2.add_input_port(InputPort("old"))
        fpo2.add_assignment(ParameterAssignment("new", "2*old"))

        fpo3 = FunctionalPortedObject("triple")
        fpo3.add_input_port(InputPort("old"))
        fpo3.add_assignment(ParameterAssignment("new", "3*old"))

        rabbits = Variable("rabbits", 1)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject("rabbit growth", [assg])
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
        cpo_eco.add_variable_aggregation_wiring(["rabbit growth.rabbits"], "rabbits")

        compiled = cpo_eco.compile()

        var, par = compiled.get_assignments()
        system = System(variable_assignments=var, parameter_assignments=par)
        system._compute_substitutions()

        system._advance_time(1)
        system._advance_time(1)
        self.assertEqual(len(system.variables), 1)
        variable = system.variables[0]
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
