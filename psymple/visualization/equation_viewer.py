"""
EquationViewer: Enhanced equation inspection and visualization for psymple
File location: psymple/visualization/equation_viewer.py

Addresses GitHub Issue #77: Equation inspection and visualisation
https://github.com/casasglobal-org/psymple/issues/77
"""

from __future__ import annotations
from typing import List, Dict, Set, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
import warnings

import sympy as sp
from sympy import Symbol, Basic, latex, Eq, Derivative

if TYPE_CHECKING:
    from psymple.build.ported_objects import CompiledPortedObject
    from psymple.build.system import System

# Import existing psymple components
from psymple.abstract import Assignment
from psymple.build.assignments import (
    DifferentialAssignment, 
    ParameterAssignment,
    FunctionalAssignment,
    DefaultParameterAssignment
)
from psymple.variables import SimVariable, SimParameter


class SubstitutionMode(Enum):
    """Modes for equation substitution."""
    NONE = "none"
    SHALLOW = "shallow"    # Substitute direct dependencies only
    DEEP = "deep"         # Substitute all dependencies recursively
    SELECTIVE = "selective"  # Use filtering criteria


class OutputFormat(Enum):
    """Supported output formats."""
    TEXT = "text"
    LATEX = "latex"
    HTML = "html"
    MARKDOWN = "markdown"
    SYMPY = "sympy"


@dataclass
class SubstitutionOptions:
    """Configuration for equation substitution behavior."""
    mode: SubstitutionMode = SubstitutionMode.SHALLOW
    max_depth: int = 10
    substitute_types: Set[type] = field(default_factory=set)
    exclude_types: Set[type] = field(default_factory=set)
    substitute_symbols: Set[Symbol] = field(default_factory=set)
    exclude_symbols: Set[Symbol] = field(default_factory=set)
    symbol_mapping: Dict[Symbol, Symbol] = field(default_factory=dict)
    def should_substitute_symbol(self, symbol: Symbol) -> bool:
        """Check if a symbol should be substituted."""
        if self.exclude_symbols and symbol in self.exclude_symbols:
            return False
        if self.substitute_symbols and symbol not in self.substitute_symbols:
            return False
        return True

    def should_substitute_type(self, obj_type: type) -> bool:
        """Check if an object type should be substituted."""
        if self.exclude_types and obj_type in self.exclude_types:
            return False
        if self.substitute_types and obj_type not in self.substitute_types:
            return False
        return True


class EquationFormatter:
    """Handles formatting equations in different output formats."""

    @staticmethod
    def format_assignment(assignment: Assignment, 
                         format_type: OutputFormat = OutputFormat.TEXT,
                         symbol_mapping: Dict[Symbol, Symbol] = None,
                         as_differential: bool = False) -> str:
        """
        Format a single assignment equation.

        Args:
            assignment: Assignment to format
            format_type: Output format
            symbol_mapping: Symbol renaming mapping
            as_differential: Whether to format as differential equation

        Returns:
            Formatted equation string
        """
        if symbol_mapping is None:
            symbol_mapping = {}

        # Apply symbol mapping
        lhs_symbol = symbol_mapping.get(assignment.symbol, assignment.symbol)
        rhs_expr = assignment.expression.subs(symbol_mapping)

        # Create left-hand side
        if as_differential:
            # Format as differential equation: dx/dt = ...
            time_symbol = symbol_mapping.get(Symbol('T'), Symbol('t'))
            lhs = Derivative(lhs_symbol, time_symbol)
        else:
            # Format as algebraic equation: x = ...
            lhs = lhs_symbol

        # Format based on output type
        if format_type == OutputFormat.TEXT:
            return f"{lhs} = {rhs_expr}"
        elif format_type == OutputFormat.LATEX:
            return f"{latex(lhs)} = {latex(rhs_expr)}"
        elif format_type == OutputFormat.HTML:
            latex_str = f"{latex(lhs)} = {latex(rhs_expr)}"
            return f'<span class="math">\\({latex_str}\\)</span>'
        elif format_type == OutputFormat.MARKDOWN:
            latex_str = f"{latex(lhs)} = {latex(rhs_expr)}"
            return f"$${latex_str}$$"
        elif format_type == OutputFormat.SYMPY:
            return Eq(lhs, rhs_expr)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    @staticmethod
    def format_system(assignments: List[Assignment],
                     format_type: OutputFormat = OutputFormat.TEXT,
                     symbol_mapping: Dict[Symbol, Symbol] = None,
                     title: str = None,
                     differential_assignments: Set[Assignment] = None) -> str:
        """
        Format a system of equations.

        Args:
            assignments: List of assignments to format
            format_type: Output format
            symbol_mapping: Symbol renaming mapping
            title: Optional system title
            differential_assignments: Set of assignments to format as differentials

        Returns:
            Formatted system string
        """
        if not assignments:
            return "No equations to display"

        if differential_assignments is None:
            differential_assignments = set()

        # Format individual equations
        equations = []
        for assignment in assignments:
            is_differential = assignment in differential_assignments
            eq_str = EquationFormatter.format_assignment(
                assignment, format_type, symbol_mapping, is_differential
            )
            equations.append(eq_str)

        # Combine equations based on format
        if format_type == OutputFormat.LATEX:
            title_part = f"\\text{{{title}}}\\\\" if title else ""
            equations_part = " \\\\\n".join(equations)
            return f"{title_part}\\begin{{align}}\n{equations_part}\n\\end{{align}}"

        elif format_type == OutputFormat.MARKDOWN:
            title_part = f"## {title}\n\n" if title else ""
            equations_part = "\n\n".join(equations)
            return f"{title_part}{equations_part}"

        elif format_type == OutputFormat.HTML:
            title_part = f"<h3>{title}</h3>\n" if title else ""
            equations_part = "<br>\n".join(equations)
            return f"{title_part}<div class=\"equation-system\">\n{equations_part}\n</div>"

        else:  # TEXT or SYMPY
            title_part = f"{title}:\n" if title else ""
            equations_part = "\n".join(equations)
            return f"{title_part}{equations_part}"


class EquationSubstitutor:
    """Handles equation substitution logic."""

    def __init__(self, assignments: List[Assignment]):
        """
        Initialize substitutor with available assignments.

        Args:
            assignments: List of all available assignments for substitution
        """
        self.assignments = assignments
        self._assignment_map = {a.symbol: a for a in assignments}
        self._dependency_cache: Dict[Symbol, Dict[Symbol, Set[Symbol]]] = {}

    def substitute_assignment(self, assignment: Assignment,
                            options: SubstitutionOptions) -> Assignment:
        """
        Apply substitution to an assignment based on options.

        Args:
            assignment: Assignment to substitute
            options: Substitution configuration

        Returns:
            New assignment with substitutions applied
        """
        if options.mode == SubstitutionMode.NONE:
            return assignment

        # Apply substitutions to expression
        substituted_expr = self._substitute_expression(
            assignment.expression, options, depth=0, visited=set()
        )

        # Apply symbol mapping to LHS
        new_symbol = options.symbol_mapping.get(assignment.symbol, assignment.symbol)

        # Create new assignment - use safe constructor approach
        if isinstance(assignment, DifferentialAssignment):
            return DifferentialAssignment(new_symbol, substituted_expr)
        elif isinstance(assignment, ParameterAssignment):
            return ParameterAssignment(new_symbol, substituted_expr)
        elif isinstance(assignment, FunctionalAssignment):
            return FunctionalAssignment(new_symbol, substituted_expr)
        elif isinstance(assignment, DefaultParameterAssignment):
            return DefaultParameterAssignment(new_symbol, substituted_expr)
        else:
            # Fallback to base Assignment
            return Assignment(new_symbol, substituted_expr)

    def _substitute_expression(self, expr: Basic, options: SubstitutionOptions,
                             depth: int, visited: Set[Symbol]) -> Basic:
        """
        Recursively substitute symbols in an expression.

        Args:
            expr: Expression to substitute
            options: Substitution options
            depth: Current recursion depth
            visited: Set of already visited symbols (prevents cycles)
 
        Returns:
            Expression with substitutions applied
        """
        # Check depth limit
        if depth >= options.max_depth:
            return expr

        # For shallow mode, only substitute at depth 0
        if options.mode == SubstitutionMode.SHALLOW and depth > 0:
            return expr

        # Apply symbol mapping first
        expr = expr.subs(options.symbol_mapping)

        # Find symbols to substitute
        symbols_to_substitute = set()
        for symbol in expr.free_symbols:
            if (symbol not in visited and 
                options.should_substitute_symbol(symbol) and
                    symbol in self._assignment_map):

                assignment = self._assignment_map[symbol]
                if options.should_substitute_type(type(assignment)):
                    symbols_to_substitute.add(symbol)

        # Perform substitutions
        substitutions = {}
        for symbol in symbols_to_substitute:
            assignment = self._assignment_map[symbol]
            new_visited = visited | {symbol}

            substituted_expr = self._substitute_expression(
                assignment.expression, options, depth + 1, new_visited
            )
            substitutions[symbol] = substituted_expr

        return expr.subs(substitutions)

    def get_dependencies(self, assignment: Assignment, max_depth: int = None) -> Dict[Symbol, Set[Symbol]]:
        """
        Get dependency graph for an assignment.

        Args:
            assignment: Assignment to analyze
            max_depth: Maximum depth for analysis

        Returns:
            Dictionary mapping symbols to their dependencies
        """
        cache_key = assignment.symbol
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]

        dependencies = {}
        visited = set()

        def _analyze_dependencies(symbol: Symbol, depth: int = 0) -> Set[Symbol]:
            if max_depth is not None and depth >= max_depth:
                return set()
            if symbol in visited:
                return dependencies.get(symbol, set())

            visited.add(symbol)
            deps = set()

            if symbol in self._assignment_map:
                assignment = self._assignment_map[symbol]
                direct_deps = assignment.expression.free_symbols
                deps.update(direct_deps)

                # Recursive analysis
                for dep in direct_deps:
                    deps.update(_analyze_dependencies(dep, depth + 1))

            dependencies[symbol] = deps
            return deps

        _analyze_dependencies(assignment.symbol)
        self._dependency_cache[cache_key] = dependencies
        return dependencies


class EquationViewer:
    """
    Main class for equation inspection and visualization.

    Provides comprehensive equation viewing, substitution, and formatting
    capabilities for psymple assignments and compiled systems.
    """

    def __init__(self, assignments: List[Assignment] = None):
        """
        Initialize the equation viewer.

        Args:
            assignments: List of assignments (variables and parameters)
        """
        self.assignments = assignments or []
        self.substitutor = EquationSubstitutor(self.assignments)
        self.formatter = EquationFormatter()

        # Separate assignments by type
        self.variable_assignments: List[Assignment] = []
        self.parameter_assignments: List[Assignment] = []
        self._categorize_assignments()

    def _categorize_assignments(self) -> None:
        """Categorize assignments by type using proper isinstance checks."""
        self.variable_assignments = []
        self.parameter_assignments = []

        for assignment in self.assignments:
            if isinstance(assignment, DifferentialAssignment):
                self.variable_assignments.append(assignment)
            else:
                self.parameter_assignments.append(assignment)

    @classmethod
    def from_compiled_object(cls, compiled_object: 'CompiledPortedObject') -> 'EquationViewer':
        """
        Create EquationViewer from a CompiledPortedObject.

        Args:
            compiled_object: CompiledPortedObject instance

        Returns:
            Configured EquationViewer instance

        Raises:
            AttributeError: If compiled_object doesn't have get_assignments method
            ValueError: If get_assignments returns invalid data
        """
        if not hasattr(compiled_object, 'get_assignments'):
            raise AttributeError("compiled_object must have get_assignments() method")

        try:
            var_assignments, param_assignments = compiled_object.get_assignments()
            all_assignments = var_assignments + param_assignments
            return cls(all_assignments)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid data from get_assignments(): {e}") from e

    @classmethod 
    def from_system(cls, system: 'System') -> 'EquationViewer':
        """
        Create EquationViewer from a System instance.

        Args:
            system: System instance (must be compiled)

        Returns:
            Configured EquationViewer instance

        Raises:
            ValueError: If system is not compiled
        """
        if not getattr(system, 'compiled', False):
            raise ValueError("System must be compiled before creating EquationViewer")

        # Convert SimVariable and SimParameter to Assignments
        assignments = []

        # Add variable assignments
        for sim_var in system.variables.values():
            if hasattr(sim_var, 'update_rule') and sim_var.update_rule:
                # Create DifferentialAssignment
                assignment = DifferentialAssignment(sim_var.symbol, sim_var.update_rule.expression)
                assignments.append(assignment)

        # Add parameter assignments  
        for sim_param in system.parameters.values():
            if hasattr(sim_param, 'value') and sim_param.value is not None:
                # Create ParameterAssignment
                assignment = ParameterAssignment(sim_param.symbol, sim_param.value)
                assignments.append(assignment)

        return cls(assignments)

    def add_assignments(self, assignments: List[Assignment]) -> None:
        """Add additional assignments to the viewer."""
        self.assignments.extend(assignments)
        self.substitutor = EquationSubstitutor(self.assignments)
        self._categorize_assignments()

    def view_equation(self, assignment: Assignment,
                     substitution_options: SubstitutionOptions = None,
                     format_type: OutputFormat = OutputFormat.TEXT) -> str:
        """
        View a single equation with optional substitution and formatting.

        Args:
            assignment: Assignment to view
            substitution_options: Substitution configuration
            format_type: Output format

        Returns:
            Formatted equation string
        """
        if substitution_options is None:
            substitution_options = SubstitutionOptions()

        # Apply substitutions
        substituted = self.substitutor.substitute_assignment(assignment, substitution_options)

        # Format and return
        is_differential = isinstance(assignment, DifferentialAssignment)
        return self.formatter.format_assignment(
            substituted, format_type, substitution_options.symbol_mapping, is_differential
        )

    def view_system(self, assignments: List[Assignment] = None,
                   substitution_options: SubstitutionOptions = None,
                   format_type: OutputFormat = OutputFormat.TEXT,
                   title: str = None,
                   variables_only: bool = False,
                   parameters_only: bool = False) -> str:
        """
        View a system of equations.

        Args:
            assignments: Specific assignments to view (default: all)
            substitution_options: Substitution configuration
            format_type: Output format
            title: Optional system title
            variables_only: Show only variable equations
            parameters_only: Show only parameter equations

        Returns:
            Formatted system string
        """
        # Select assignments to display
        if assignments is None:
            if variables_only:
                assignments = self.variable_assignments
            elif parameters_only:
                assignments = self.parameter_assignments
            else:
                assignments = self.assignments

        if not assignments:
            return "No equations to display"

        if substitution_options is None:
            substitution_options = SubstitutionOptions()

        # Apply substitutions to all assignments
        substituted_assignments = [
            self.substitutor.substitute_assignment(a, substitution_options)
            for a in assignments
        ]

        # Identify which assignments should be formatted as differentials
        differential_assignments = {
            sub_a for orig_a, sub_a in zip(assignments, substituted_assignments)
            if isinstance(orig_a, DifferentialAssignment)
        }

        # Format system
        return self.formatter.format_system(
            substituted_assignments, format_type, 
            substitution_options.symbol_mapping, title, differential_assignments
        )

    def get_dependencies(self, assignment: Assignment = None,
                        symbol: Symbol = None,
                        max_depth: int = None) -> Dict[Symbol, Set[Symbol]]:
        """
        Get dependency graph for an assignment or symbol.

        Args:
            assignment: Assignment to analyze (takes precedence)
            symbol: Symbol to analyze
            max_depth: Maximum analysis depth

        Returns:
            Dictionary mapping symbols to their dependencies

        Raises:
            ValueError: If neither assignment nor symbol is provided
        """
        if assignment is not None:
            return self.substitutor.get_dependencies(assignment, max_depth)
        elif symbol is not None:
            # Find assignment for symbol
            for assignment in self.assignments:
                if assignment.symbol == symbol:
                    return self.substitutor.get_dependencies(assignment, max_depth)
            return {symbol: set()}  # No dependencies found
        else:
            raise ValueError("Must provide either assignment or symbol")

    def create_readable_symbols(self, 
                              var_prefix: str = "x",
                              param_prefix: str = "p",
                              keep_short_names: bool = True) -> Dict[Symbol, Symbol]:
        """
        Create human-readable symbol mappings.

        Args:
            var_prefix: Prefix for variable symbols
            param_prefix: Prefix for parameter symbols  
            keep_short_names: Keep symbols with names <= 3 characters unchanged

        Returns:
            Mapping from original symbols to readable symbols
        """
        mapping = {}
        var_counter = 1
        param_counter = 1

        # Process variable assignments
        for assignment in self.variable_assignments:
            symbol = assignment.symbol
            if symbol not in mapping:
                if keep_short_names and len(symbol.name) <= 3:
                    mapping[symbol] = symbol
                else:
                    mapping[symbol] = Symbol(f"{var_prefix}_{var_counter}")
                    var_counter += 1

        # Process parameter assignments
        for assignment in self.parameter_assignments:
            symbol = assignment.symbol
            if symbol not in mapping:
                if keep_short_names and len(symbol.name) <= 3:
                    mapping[symbol] = symbol
                else:
                    mapping[symbol] = Symbol(f"{param_prefix}_{param_counter}")
                    param_counter += 1

        return mapping

    def summary(self) -> str:
        """Get a summary of the equation system."""
        var_count = len(self.variable_assignments)
        param_count = len(self.parameter_assignments)
        total = len(self.assignments)

        return (f"EquationViewer Summary:\n"
                f"  Variables: {var_count}\n"
                f"  Parameters: {param_count}\n"
                f"  Total equations: {total}")


# Convenience functions for backward compatibility and easy integration
def create_equation_viewer(assignments: List[Assignment]) -> EquationViewer:
    """Convenience function to create an EquationViewer."""
    return EquationViewer(assignments)


def view_equations(assignments: List[Assignment],
                  format_type: OutputFormat = OutputFormat.TEXT,
                  title: str = None) -> str:
    """Convenience function to quickly view equations."""
    viewer = EquationViewer(assignments)
    return viewer.view_system(format_type=format_type, title=title)


# Integration helpers for existing psymple classes
def enhance_sim_variable_readout(sim_variable: SimVariable, **kwargs) -> str:
    """Enhanced readout for SimVariable using EquationViewer."""
    if hasattr(sim_variable, 'update_rule') and sim_variable.update_rule:
        assignment = DifferentialAssignment(sim_variable.symbol, sim_variable.update_rule.expression)
        viewer = EquationViewer([assignment])
        return viewer.view_equation(assignment, **kwargs)
    else:
        return f"{sim_variable.symbol} = [no update rule]"


def enhance_sim_parameter_readout(sim_parameter: SimParameter, **kwargs) -> str:
    """Enhanced readout for SimParameter using EquationViewer."""
    if hasattr(sim_parameter, 'value') and sim_parameter.value is not None:
        assignment = ParameterAssignment(sim_parameter.symbol, sim_parameter.value)
        viewer = EquationViewer([assignment])
        return viewer.view_equation(assignment, **kwargs)
    else:
        return f"{sim_parameter.symbol} = [no value]"
