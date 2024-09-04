from sympy import Symbol

class SymbolIdentification:
    """
    Class formally identifying two symbols as equal.

    warning: Warning
        This class should not be instantiated directly. It is automatically created
        and accessed when required.
    """
    def __init__(self, new_symbol: Symbol, old_symbol: Symbol):
        """
        Create a symbol identification.

        Args:
            new_symbol: the new symbol
            old_symbol: the symbol to replace
        """
        self.old_symbol = old_symbol
        self.new_symbol = new_symbol

    def __repr__(self):
        return f"SymbolIdentification {self.new_symbol} = {self.old_symbol}"

class VariableAggregationWiring:
    """
    Stores the connection of child variable ports in a composite ported object to
    a specified parent port or internal variable.

    warning: Warning
        This class should not be instantiated on its own. Instead, use
        [`psymple.build.CompositePortedObject.add_variable_wire`][] or 
        [`psymple.build.CompositePortedObject.add_wires`][].
    """

    def __init__(self, child_ports: list[str], parent_port: str, output_name: str):
        """
        Create a variable wire.

        Args:
            child_ports: list of ports whose variables will be aggregated.
            parent_port: variable port to expose the aggregation.
            output_name: name to assign internally to the aggregation if it is
                not exposed.
        """
        self.child_ports = child_ports
        self.parent_port = parent_port
        self.output_name = output_name

    def _to_data(self):
        data = {
            "child_ports": self.child_ports,
            "parent_port": self.parent_port,
            "output_name": self.output_name,
        }
        return data


class DirectedWire:
    """
    Stores the connection of an input port or child output port in a composite ported
    object to a child input ports and/or an output port.

    warning: Warning
        This class should not be instantiated on its own. Instead, use
        [`psymple.build.CompositePortedObject.add_directed_wire`][] or 
        [`psymple.build.CompositePortedObject.add_wires`][].
    """

    def __init__(self, source_port: str, destination_ports: list[str]):
        """
        Create a directed wire.

        Args:
            source_port: initial port which the wire reads from.
            destination_ports: list of ports to which the read value is provided.
        """
        self.source_port = source_port
        self.destination_ports = destination_ports

    def _to_data(self):
        data = {
            "source": self.source_port,
            "destinations": self.destination_ports,
        }
        return data