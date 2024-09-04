import unittest

import sympy as sym

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
)

class TimeDepdendentPredatorPrey(unittest.TestCase):
    prey = CompositePortedObject(
        name="prey",
        children=[
            FunctionalPortedObject(
                name="birth",
                assignments=[("rate", "0.5*(sin(T)+1)")],
            ),
            VariablePortedObject(
                name="growth",
                assignments=[("x", "r*x")],
            )
        ],
        variable_ports=["prey"],
        directed_wires=[("birth.rate", "growth.r")],
        variable_wires=[(["growth.x"], "prey")],
    )

    pred = CompositePortedObject(
        name="pred",
        children=[
            FunctionalPortedObject(
                name="mortality",
                assignments=[("rate", "0.5*(cos(T)+1)")],
            ),
            VariablePortedObject(
                name="decline",
                assignments=[("x", "-r*x")],
            )
        ],
        variable_ports=["pred"],
        directed_wires=[("mortality.rate", "decline.r")],
        variable_wires=[(["decline.x"], "pred")],
    )

    pred_prey = VariablePortedObject(
        name="pred_prey",
        input_ports=[("r_1", 0.5), ("r_2", 0.1)],
        assignments=[
            ("prey", "-r_1 * pred * prey"),
            ("pred", "r_2 * pred * prey")
        ]
    )

    system = CompositePortedObject(
        name="system",
        children=[pred, prey, pred_prey],
        variable_ports=["pred", "prey"],
        variable_wires=[
            (["prey.prey", "pred_prey.prey"], "prey"),
            (["pred.pred", "pred_prey.pred"], "pred"),
        ]
    )