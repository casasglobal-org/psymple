import sympy as sym

from ..build import HIERARCHY_SEPARATOR

class Port:
    """
    Base class for all ports. 

    Ports are key to the definition of ported objects. A ported object can be
    thought of as a container for some information. A port exposes some of that
    information, labeled by an identifier, to the exterior of that object.
    
    Different implementations of ports expose different information in different
    ways.

    warning: Warning
        The `Port` class should not be instantiated directly.
    
    info: Note
        The name of a port uniquely determines its symbol. The symbol only has relevance 
        in two cases:    
        
        - Input port symbols for `VariablePortedObject` and `FunctionalPortedObject` 
            instances. In this case, the symbol may appear in expressions defined within 
            those objects, and input values will be substituted into it.
        
        - Variable port symbols when the variable port is not connected on the outside. 
            This symbol will then become globally associated to the variable that is
            simulated in the system.
    """

    def __init__(self, name: str , description: str = ""):
        """
        Initialise a Port.

        Args:
            name: the identifier of a port associated to a [`PortedObject`][psymple.build.abstract.PortedObject]
            description: a description of the contents of a port 

        Raises:
            ValueError: if an invalid name is given. By default, this is any string containing a period `"."`.
        """
        if HIERARCHY_SEPARATOR in name:
            raise ValueError(
                f"Port '{name}': Port names must not contain '{HIERARCHY_SEPARATOR}'."
            )
        self.name = name
        self.description = description

    @property
    def symbol(self):
        return sym.Symbol(self.name)

    def __repr__(self):
        return f"{type(self).__name__} {self.name}"
    
    def _to_data(self):
        data = {
            "name": self.name,
            "description": self.description
        }
        return data


class VariablePort(Port):
    """
    A variable port is a port exposing a system variable.
    """
    pass


class InputPort(Port):
    """
    An input port is a port exposing a system parameter which can be provided a value.
    """
    def __init__(self, name, description="", default_value=None):
        super().__init__(name, description)
        self.default_value = default_value

    def _to_data(self):
        data = super()._to_data()
        data.update(
            {
                "default_value": self.default_value
            }
        )
        return data


class OutputPort(Port):
    """
    An output port is a port exposing a system parameter which can be read from.
    """
    pass