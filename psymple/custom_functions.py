import math

import numpy as np
import sympy as sym
from scipy.optimize import root_scalar
from sympy.abc import x, a, b
from sympy import integrate, sympify
from psymple import read_wx

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
    

wx = read_wx.Weather.readwx("c:\\Users\\georg\\OneDrive\\Documents\\IDEMS\\CASAS Global\\Modelling\\Python\\population-modeling-py-3\\examples\\pbdm\\sample_weather.txt","01","01","2000","12","31","2010", [0])[1:]
wx = np.array(wx)

def temp_max_fun(
    time: float,
    temperature_data = wx
):
    model_day = math.ceil(time)
    return temperature_data[model_day][5]

def temp_min_fun(
    time: float,
    temperature_data = wx
):
    model_day = math.ceil(time)
    return temperature_data[model_day][6]

def solar_rad_fun(
    time: float,
    temperature_data = wx
):
    model_day = math.ceil(time)
    return temperature_data[model_day][7]

def temp_fun(
    time: float,
):
    temp_max = temp_max_fun(time)
    temp_min = temp_min_fun(time)
    #return (temp_max - temp_min)/2 * np.sin(np.float64(2*np.pi*(time+1/4))) + (temp_max + temp_min)/2
    return (temp_max + temp_min)/2


class temp_max(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, time):
        if isinstance(time, sym.Float) and time < 0:
            return 0

    def _eval_evalf(self, prec):
        return sym.Float(temp_max_fun(*self.args))._eval_evalf(prec)

class temp_min(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, time):
        if isinstance(time, sym.Float) and time < 0:
            return 0

    def _eval_evalf(self, prec):
        return sym.Float(temp_min_fun(*self.args))._eval_evalf(prec)
    
class solar_rad(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, time):
        if isinstance(time, sym.Float) and time < 0:
            return 0

    def _eval_evalf(self, prec):
        return sym.Float(solar_rad_fun(*self.args))._eval_evalf(prec)

class temp(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, time):
        if isinstance(time, sym.Float) and time < 0:
            return 0

    def _eval_evalf(self, prec):
        return sym.Float(temp_fun(*self.args))._eval_evalf(prec)
    
def DD_fun(time, Del, T_min, T_max = 0, coeff_1 = 0, coeff_2 = 0):
    T = temp_fun(time)
    if T_max < T_min:
        return np.maximum(0.01,T-T_min)
    else:
        return np.maximum(0, Del*(coeff_1*(T-T_min)/(1+ coeff_2**(T - T_max))))

class DD(sym.Function):
    #TODO: this could have a doit() method
    @classmethod
    def eval(cls, time, Del, T_min, T_max = None, coeff_1 = None, coeff_2 = None):
        if isinstance(time, sym.Float) and time < 0:
            return 0

    def doit(self, deep=False, **hints):
        time, *args = self.args
        if deep:
            time = time.doit(deep=deep, **hints)
        return sym.Float(DD_fun(time, *args))

    def _eval_evalf(self, prec):
        return self.doit(deep=False)._eval_evalf(prec)
        #return sym.Float(DD_fun(*self.args))._eval_evalf(prec) 
        #T = temp_fun(time)
        #return sym.Float(DD_fun(time=self.args[0], Del = self.args[1], T_min = self.args[2], T_max = self.args[3], coeff_1 = self.args[4], coeff_2 = self.args[5]))._eval_evalf(prec)

def ind_above_fun(base, comp):
    return 1 if comp>base else 0

class ind_above(sym.Function):
    @classmethod
    def eval(cls, base, comp):
        return ind_above_fun(base, comp)

def frac0_fun(numerator, denominator, default):
    return default if denominator == 0 else numerator/denominator

class frac0(sym.Function):
    @classmethod
    def eval(cls, numerator, denominator, default):
        if denominator == 0:
            return default