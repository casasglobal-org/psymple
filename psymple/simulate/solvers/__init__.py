from .discrete_integrator import DiscreteIntegrator
from .scipy_integrator import ContinuousIntegrator

SOLVER_ALIASES = {
    "discrete": [
        "discrete",
        "discrete",
        "dscr",
        "disc",
        "discr",
    ],
    "continuous": [
        "continuous",
        "cts",
        "cont",
        "scipy",
    ],
    "proceedural": [
        "proceedural",
        "proc",
    ],
}