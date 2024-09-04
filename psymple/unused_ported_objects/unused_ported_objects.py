from build.abstract import PortedObject
from build import VariablePortedObject
from build.assignments import DifferentialAssignment


class SymbolPortedObject(VariablePortedObject):
    def __init__(self, name: str):
        assignment = DifferentialAssignment(name, 0)
        super().__init__(name, [assignment])


class ODECreatorPortedObject(PortedObject):
    def __init__(self):
        self.input_ports  # expr, variable
        self.variable_ports  # output

    def compile(self, global_symbols=set()):
        # d var / d t = expression
        # if the input variable name differs from the port,
        # create an identification assignment
        pass


class RHSExpressionPortedObject(PortedObject):
    # A variable comes in, an expression comes out
    def __init__(self):
        self.input_ports  # expr, variable
        self.output_ports  # output

    def compile(self, global_symbols=set()):
        # assert that the input is a variable
        # output = input.rhs
        pass


class OperatorPortedObject(PortedObject):
    # abstract class
    def __init__(self, input_port_names, output_port_name):
        pass


class PlusOperatorPortedObject(OperatorPortedObject):
    def compile(self, global_symbols=set()):
        # Make an assignment that sums up the input
        pass
