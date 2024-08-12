import unittest
import sympy as sym

# from psymple.populations import Population
# from psymple.variables import SimVariable, SimParameter, SimUpdateRule
from psymple.abstract import DependencyError
from psymple.variables import Variable

#from psymple.system import SystemError, System, Simulation, DiscreteIntegrator
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
    FunctionalAssignment,
    Port,
    PortedObject,
    VariableAggregationWiring,
    VariablePort,
    VariablePortedObject,
    WiringError,
)





class TestInitialization(unittest.TestCase):

    def test_functional2x2(self):
        fpo = FunctionalPortedObject(
            name="operations",
            input_ports=[InputPort("in1"), InputPort("in2")],
            assignments=[
                FunctionalAssignment("sum", "in1+in2"),
                FunctionalAssignment("prod", "in1*in2"),
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
        vpo_growth = VariablePortedObject("rabbit growth", assignments=[assg])

        compiled = vpo_growth.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIsInstance(rabbit_port, CompiledPort)
        self.assertEqual(rabbit_port.assignment.expression, 0.1 * sym.Symbol("rabbits"))

    def test_unexposed_variable(self):

        vpo = VariablePortedObject(
            "second_order", 
            variable_ports=["x"],
            assignments=[("x", "0.1*y"), ("y", "x")],
        )

        compiled = vpo.compile()
        self.assertIn("y", compiled.internal_variable_assignments)
        assg = compiled.internal_variable_assignments["y"]
        self.assertEqual(assg.expression, sym.Symbol("x"))

        self.assertIn("x", compiled.variable_ports)
        assg = compiled.variable_ports["x"].assignment
        self.assertEqual(assg.expression, 0.1 * sym.Symbol("y"))

    def test_variable_with_input(self):
        # To test: validation that all free parameters are inputs.
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject(
            "rabbit growth", assignments=[assg], create_input_ports=False
        )

        # r_growth has no corresponding input port yet
        with self.assertRaises(DependencyError):
            compiled = rabbit_growth.compile()

        rabbit_growth.add_input_ports(InputPort("r_growth", default_value=0.01))

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
        vpo_growth = VariablePortedObject("rabbit growth", assignments=[assg])

        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, -0.05 * sym.Symbol("rabbits")
        )  # 0.05 is the death rate
        vpo_death = VariablePortedObject("rabbit death", assignments=[assg])

        cpo_rabbits = CompositePortedObject("rabbit system")
        cpo_rabbits.add_children(vpo_growth, vpo_death)
        cpo_rabbits.add_variable_ports(VariablePort("rabbits"))
        cpo_rabbits.add_variable_wire(
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
        vpo_1 = VariablePortedObject("flow1", assignments=[assg1, assg2])

        inn = Variable("in", 50)
        out = Variable("out", 75)
        assg2 = DifferentialAssignment(
            inn, -0.2 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        assg1 = DifferentialAssignment(
            out, 0.2 * sym.Symbol("in")
        )  # 0.1 is the growth rate
        vpo_2 = VariablePortedObject("flow2", assignments=[assg1, assg2])

        cpo = CompositePortedObject("flow system")
        cpo.add_children(vpo_1, vpo_2)
        # unexposed flow transition variable
        cpo.add_variable_wire(
            ["flow1.out", "flow2.in"], output_name="mass"
        )
        # Exposed inflow variable
        cpo.add_variable_ports(VariablePort("inflow"))
        cpo.add_variable_wire(["flow1.in"], "inflow")

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

    def test_input_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject(
            "rabbit growth", assignments=[assg], create_input_ports=False
        )
        growth_input_port = InputPort("r_growth", default_value=0.01)
        rabbit_growth.add_input_ports(growth_input_port)

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_children(rabbit_growth)
        cpo_eco.add_variable_ports(VariablePort("rabbits"))
        cpo_eco.add_variable_wire(["rabbit growth.rabbits"], "rabbits")

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
        cpo_eco.add_input_ports(InputPort("r_growth"))
        cpo_eco.add_directed_wire("r_growth", ["rabbit growth.r_growth"])
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

    """
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

    def test_output_forwarding(self):
        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(rabbits, 0.01 * sym.Symbol("rabbits"))
        rabbit_growth = VariablePortedObject(name="rabbit growth", assignments=[assg])

        fpo = FunctionalPortedObject(
            name="double",
            assignments=[FunctionalAssignment("new", "2*old")],
            create_input_ports=True,
        )


        cpo_eco = CompositePortedObject(
            name="ecosystem",
            children=[rabbit_growth, fpo],
            variable_ports=[VariablePort("rabbits")],
            output_ports=[OutputPort("doublerab")],
            variable_wires=[(["rabbit growth.rabbits"], "rabbits")],
            directed_wires=[
                ("rabbit growth.rabbits", "double.old"),
                ("double.new", "doublerab")
            ]
        )

        compiled = cpo_eco.compile()
        self.assertIn("rabbits", compiled.variable_ports)
        rabbit_port = compiled.variable_ports["rabbits"]
        self.assertIn("doublerab", compiled.output_ports)
        doublerab_port = compiled.output_ports["doublerab"]
        double_assg = doublerab_port.assignment
        self.assertEqual(rabbit_port.symbol, sym.Symbol("rabbits"))
        self.assertEqual(doublerab_port.symbol, sym.Symbol("doublerab"))
        self.assertEqual(double_assg.symbol, sym.Symbol("doublerab"))
        self.assertEqual(
            double_assg.expression,
            2 * sym.Symbol("rabbits"),
        )

    def test_output_nesting(self):
        # TODO: Add checks
        A_func = FunctionalPortedObject(
            name="func",
            input_ports=[InputPort("X", default_value=5)],
            assignments=[FunctionalAssignment("Y", "X")]
        )

        A = CompositePortedObject(
            name="A",
            children=[A_func],
            output_ports=[OutputPort("Y")],
            directed_wires=[("func.Y", "Y")]
        )

        B = CompositePortedObject(
            name="B",
            children=[A],
            output_ports=[OutputPort("BY")],
            directed_wires=[("A.Y", "BY")]
        )

        compiled = B.compile()

    def test_parameters(self):
        fpo = FunctionalPortedObject("double")
        fpo.add_input_ports(InputPort("old"))
        fpo.add_parameter_assignments(FunctionalAssignment("new", "2*old"))

        rabbits = Variable("rabbits", 50)
        assg = DifferentialAssignment(
            rabbits, sym.Symbol("r_growth") * sym.Symbol("rabbits")
        )
        rabbit_growth = VariablePortedObject(
            "rabbit growth", assignments=[assg], create_input_ports=False
        )
        rabbit_growth.add_input_ports(InputPort("r_growth"))

        cpo_eco = CompositePortedObject("ecosystem")
        cpo_eco.add_children(rabbit_growth, fpo)
        cpo_eco.add_input_ports(InputPort("r_growth", default_value=0.01))
        cpo_eco.add_directed_wire("r_growth", ["double.old"])
        cpo_eco.add_directed_wire("double.new", ["rabbit growth.r_growth"])
        cpo_eco.add_variable_ports(VariablePort("rabbits"))
        cpo_eco.add_variable_wire(["rabbit growth.rabbits"], "rabbits")

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
        func_1.add_input_ports(InputPort("X", default_value=5))
        func_1.add_parameter_assignments(FunctionalAssignment("Y", "X"))

        A = CompositePortedObject("A")
        A.add_children(func_1)
        A.add_input_ports(InputPort("X", default_value=3))
        A.add_output_ports(OutputPort("Y"))
        A.add_directed_wire("X", ["func_1.X"])
        A.add_directed_wire("func_1.Y", ["Y"])

        B = CompositePortedObject("B")
        B.add_children(A)
        B.add_input_ports(InputPort("X", default_value=1))
        B.add_output_ports(OutputPort("Y"))
        B.add_directed_wire("X", ["A.X"])
        B.add_directed_wire("A.Y", ["Y"])

        C = CompositePortedObject("C")
        C.add_children(B)

        compiled = C.compile()


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
