"""
Visualization tools for psymple equations and systems.

This module provides enhanced equation inspection and visualization capabilities
for psymple complex systems models, addressing GitHub Issue #77.

Main Components:
    EquationViewer: Main class for equation inspection and visualization
    SubstitutionOptions: Configuration for equation substitution behavior
    SubstitutionMode: Enumeration of substitution modes
    OutputFormat: Enumeration of supported output formats

Example:
    >>> from psymple.visualization import EquationViewer, SubstitutionOptions, OutputFormat
    >>> viewer = EquationViewer(assignments)
    >>> options = SubstitutionOptions(mode=SubstitutionMode.DEEP)
    >>> result = viewer.view_system(substitution_options=options, format_type=OutputFormat.LATEX)
"""

# Core classes and enums
from .equation_viewer import (
    # Main classes
    EquationViewer,
    SubstitutionOptions,
    EquationFormatter,
    EquationSubstitutor,

    # Enums
    SubstitutionMode,
    OutputFormat,

    # Convenience functions
    create_equation_viewer,
    view_equations,
)

# Define public API
__all__ = [
    # Main classes
    "EquationViewer",
    "SubstitutionOptions", 
    "EquationFormatter",
    "EquationSubstitutor",

    # Enums
    "SubstitutionMode",
    "OutputFormat",

    # Convenience functions
    "create_equation_viewer",
    "view_equations",
]

# Module metadata
__version__ = "1.0.0"
__author__ = "Psymple Contributors"
__description__ = "Enhanced equation inspection and visualization for psymple"

# For backward compatibility and convenience
def quick_view(assignments, format_type="text", title=None):
    """
    Quick function to view equations without creating EquationViewer instance.

    Args:
        assignments: List of Assignment objects
        format_type: Output format ("text", "latex", "html", "markdown")
        title: Optional title for the system

    Returns:
        Formatted equation system string

    Example:
        >>> quick_view(my_assignments, format_type="latex", title="My Model")
    """
    format_map = {
        "text": OutputFormat.TEXT,
        "latex": OutputFormat.LATEX,
        "html": OutputFormat.HTML,
        "markdown": OutputFormat.MARKDOWN
    }

    return view_equations(
        assignments, 
        format_type=format_map.get(format_type, OutputFormat.TEXT),
        title=title
    )


# Add quick_view to public API
__all__.append("quick_view")
