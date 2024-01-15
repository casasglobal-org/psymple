import sympy as sym
from psymple.custom_functions import DegreeDays, FFTemperature

# from custom_functions import DegreeDays, FFTemperature


# The dictionary passed to sym.sympify and sym.lambdify to convert custom functions
# TODO: This should not be a global property.
#sym_custom_ns = {}
sym_custom_ns = {'DegreeDays': DegreeDays, 'FFTemperature': FFTemperature}


T = sym.Symbol("T")
