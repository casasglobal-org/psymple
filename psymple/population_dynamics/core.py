from psymple.build import (
    VariablePortedObject,
    FunctionalPortedObject,
    CompositePortedObject,
)

class Summation(FunctionalPortedObject):
    def __init__(self, *summands, name="summation"):
        super().__init__(
            name=name,
            assignments=[
                ("sum", "+".join(summands)),
            ]
        )
    
    @property
    def sum(self):
        return f"{self.name}.sum"

class MalthusianBase(VariablePortedObject):
    def __init__(self, name="malthusian_var", rate=None, variable_symbol="x", rate_symbol="r"):
        self.variable_symbol = variable_symbol
        self.rate_symbol = rate_symbol
        input_ports = []
        if rate:
            input_ports.append(
                {
                    "name": rate_symbol,
                    "default_value": rate,
                }
            )
        super().__init__(
            name=name,
            assignments=[
                {
                    "variable": variable_symbol,
                    "expression": f"{rate_symbol}*{variable_symbol}",
                }
            ],
            input_ports=input_ports,
        )

    @property
    def variable(self):
        return f"{self.name}.{self.variable_symbol}"

    @property
    def rate(self):
        return f"{self.name}.{self.rate_symbol}"


class MalthusianPopulation(CompositePortedObject):
    def __init__(
        self,
        name,
        birth_rate=0,
        death_rate=0,
        variable_symbol="x",
        birth_rate_symbol="b",
        death_rate_symbol="d",
    ):
        var_object = MalthusianBase()
        rate_object = Summation(birth_rate_symbol, f"-1*{death_rate_symbol}")
        super().__init__(
            name=name,
            children=[var_object, rate_object],
            input_ports=[
                {
                    "name": birth_rate_symbol,
                    "default_value": birth_rate,
                },
                {
                    "name": death_rate_symbol,
                    "default_value": death_rate
                }
            ],
            variable_ports=[variable_symbol],
            directed_wires=[
                {
                    "source": birth_rate_symbol,
                    "destination": f"{rate_object.name}.{birth_rate_symbol}",
                },
                {
                    "source": death_rate_symbol,
                    "destination": f"{rate_object.name}.{death_rate_symbol}",
                },
                {
                    "source": rate_object.sum,
                    "destination": var_object.rate,
                },
            ],
            variable_wires=[
                {
                    "child_ports": [var_object.variable],
                    "parent_port": variable_symbol,
                }     
            ],
        )
        