
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from psymple.simulate import Simulation
    
from abc import ABC, abstractmethod

class Solver(ABC):
    """
    Base class for system integrators. All subclasses must implement a `run` method.
    """
    def __init__(self, simulation: Simulation, t_end: int):
        """
        Instantiate a solver.

        Args:
            simulation: an instance of `Simulation` to solve.
            t_end: positive integer at which to stop the simulation.
        """
        if t_end <= 0 or not isinstance(t_end, int):
            raise ValueError(
                "Simulation time must terminate at a positive integer, "
                f"not '{t_end}'."
            )
        self.t_end = t_end
        self.simulation = simulation

    @abstractmethod
    def run(self):
        pass