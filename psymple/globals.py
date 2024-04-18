import sympy as sym
from psymple.custom_functions import (
    DegreeDays,
    FFTemperature,
    temp,
    DD,
    temp_fun,
    DD_fun,
    solar_rad_fun,
    ind_above_fun,
    frac0_fun,
    temp_min_fun,
)

# from custom_functions import DegreeDays, FFTemperature


# The dictionary passed to sym.sympify and sym.lambdify to convert custom functions
# TODO: This should not be a global property.
# sym_custom_ns = {}
sym_custom_ns = {
    "DegreeDays": DegreeDays,
    "FFTemperature": FFTemperature,
    "temp": temp_fun,
    "temp_min": temp_min_fun,
    "DD": DD_fun,
    "solar_rad": solar_rad_fun,
    "ind_above": ind_above_fun,
    "frac0": frac0_fun,
}


T = sym.Symbol("T")
