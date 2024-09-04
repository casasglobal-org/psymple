import sympy as sym

from copy import deepcopy

from .assignments import (
    Assignment,
)

from .ports import (
    Port,
    InputPort,
)


class CompiledPort(Port):
    """A port object together with the assignment it exposes.

    Note:
        This class is not designed to be instantiated directly.
    """
    def __init__(self, port: Port, assignment: Assignment):
        """
        Instantiate from a port and assignment.

        Args:
            port: port to compile
            assignment: assignment to assign to the port
        """
        self.name = port.name
        self.assignment = deepcopy(assignment)
        self.description = port.description

    def substitute_symbol(self, old_symbol, new_symbol):
        if self.assignment:
            self.assignment.substitute_symbol(old_symbol, new_symbol)
            # In case the symbol of this port itself was substituted,
            # this will be reflected in the assignment, and we can pull
            # the updated name from there.
            self.name = self.assignment.name
        else:
            assert isinstance(old_symbol, sym.Symbol)
            assert isinstance(new_symbol, sym.Symbol)
            assert isinstance(self.symbol, sym.Symbol)
            if self.symbol == old_symbol:
                self.name = new_symbol.name

    def __repr__(self):
        return f"{type(self).__name__} {self.name} with {self.assignment}"


class CompiledVariablePort(CompiledPort):
    pass


class CompiledOutputPort(CompiledPort):
    pass


class CompiledInputPort(CompiledPort):
    def __init__(self, port):
        assert isinstance(port, InputPort)
        super().__init__(port, None)
        self.default_value = port.default_value

    