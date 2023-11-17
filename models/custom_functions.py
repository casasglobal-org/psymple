import math

import numpy as np
import sympy as sym
from scipy.optimize import root_scalar
from sympy.abc import x, a, b
from sympy import integrate, sympify

T = sym.Symbol("T")

# test_temps = [
#     [
#         round(20 + 5*(0.5 - random.random()), 1),
#         round(5 + 5*(0.5 - random.random()), 1),
#     ] for i in range(10)
# ]

test_temps = [
    [19.5, 3.8],
    [20.3, 7.3],
    [22.4, 6.2],
    [21.4, 5.6],
    [17.9, 2.7],
    [21.4, 3.5],
    [20.4, 2.9],
    [19.4, 6.7],
    [19.3, 6.7],
    [20.4, 8.3],
]


def DegreeDays_fun(
    model_day: float, base_temp: float, temperature_data: list = test_temps
):
    integral = None
    model_day = math.floor(model_day)
    base_temp = float(base_temp)
    if model_day == 1:
        temp_max_prev = temperature_data[model_day - 1][0]
    else:
        temp_max_prev = temperature_data[model_day - 2][0]
    temp_max, temp_min = temperature_data[model_day - 1]

    def sin_interpolate_minus_base(x, a, b):
        return (b - a) / 2 * np.sin(2 * np.pi * (x + 1 / 4)) + (b + a) / 2 - base_temp
    
    if not integral:
        integral = integrate(sympify('(b - a) / 2 * sin(2 * pi * (x + 1 / 4)) + (b + a) / 2 - c'), x)

    if base_temp <= temp_min:
        return (temp_max_prev + temp_max)/4 + temp_min/2 - base_temp

    result = 0
    for i, max in enumerate([temp_max_prev, temp_max]):
        if base_temp < max:
            root = root_scalar(
                sin_interpolate_minus_base, args=(temp_min, max), bracket=(i/2, (i+1)/2)
            )
            integral_eval = integral.subs({'a': temp_min, 'b': max, 'c': base_temp})
            area = (integral_eval.subs({'x': i}) - integral_eval.subs({'x': root.root})).evalf()
            result += (-1)**(i+1) * area
    return result


class DegreeDays(sym.Function):
    """
    SymPy wrapper for DegreeDays_fun(). When called with SymPy symbolic argument 'T',
    it returns a SymPy function object which can be
    symbolically manipulated and lambdified. When called with all float arguments it
    returns the evaluated DegreeDays_fun().
    TODO: implement derivative method for stability analysis.
    TODO: can Sympy functions accept eg. list arguments?
    """

    @classmethod
    def eval(cls, model_day, base_temp):
        """
        Defines behaviour of function on specific inputs, eg. in this case negative
        model day returns 0.
        When eval() method returns None, SymPy function returns a symbolic expression
        of the function.
        """
        if isinstance(model_day, sym.Float) and model_day < 0:
            return 0

    def _eval_evalf(self, prec):
        """
        Defines numeric evalation behaviour when function is called with float inputs.
        Required to implement lambdify behaviour.
        """
        day, base_temp = self.args
        result = DegreeDays_fun(day, base_temp)
        return sym.Float(result)._eval_evalf(prec)
    

def FFTemperature_fun(
    model_day: float,
    temp_min: float,
    temp_max: float,
    temperature_data: list = test_temps,
):
    model_day = math.floor(model_day)
    temp = (temperature_data[model_day][0] + temperature_data[model_day][1]) / 2
    if temp <= temp_min or temp >= temp_max:
        return 0
    else:
        diff = (temp_max - temp_min) / 2
        return np.max((0.0, 1 - ((temp - temp_min - diff) / diff) ** 2))


class FFTemperature(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, model_day, temp_min, temp_max):
        if isinstance(model_day, sym.Float) and model_day < 0:
            return 0

    def _eval_evalf(self, prec):
        return sym.Float(FFTemperature_fun(*self.args))._eval_evalf(prec)