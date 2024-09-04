from sympy import (
    Basic,
    Eq,
    Derivative,
    Symbol,
    lambdify,
    latex,
)

from psymple.abstract import (
    DependencyError, 
    ExpressionWrapper,
    SymbolWrapper,
)

class Container(dict):
    """
    A simple `dict` subclass for storing objects with keys `sympy.Symbol` instances
    which allows access via their string equivalents.
    """
    def __getitem__(self, item):
        if isinstance(item, str):
           item = Symbol(item)
        return super().__getitem__(item)       

class Variable(SymbolWrapper):
    """
    A variable is a [`SymbolWrapper`][psymple.abstract.SymbolWrapper] instance together with a description.
    """
    pass

class Parameter(SymbolWrapper):
    """
    A parameter is a [`SymbolWrapper`][psymple.abstract.SymbolWrapper] instance together with an 
    equivalent value and description.
    """
    def __init__(self, symbol: str | Symbol, value: str | float | Basic, description: str = ""):
        """
        Create a Parameter instance.

        Args:
            symbol: the symbol to wrap.
            value: the value represented by `symbol`.
            description: an optional description of the container contents.
        """
        super().__init__(symbol, description)
        self.value = value

class UpdateRule(ExpressionWrapper):
    """
    An update rule is an `ExpressionWrapper` that is attached to a `Variable` or `Parameter`
    instance. It stores how the variable or parameter will evolve over time. An update rule
    tracks the other variables or parameters which appear in its expression, so that it is
    fully aware of its system dependencies.

    Methods:
        sub_symbols: substitute the symbols contained inside `self`.
    """
    def __init__(
        self,
        expression: Basic | str | float | int = 0,
        variables: set = set(),
        parameters: set = set(),
        description: str = "",
    ):
        """
        Create an UpdateRule instance.

        Args:
            expression: the expression to wrap. If it is not a `sympy` object, it is 
                parsed into one first.
            variables: a set of variables of which the variables in the expression are a subset
            parameters: a set of parameters of which the parameters in the expression are a subset
            description: description of the rule
        """
        super().__init__(expression)
        self._initialise_dependencies(variables, parameters)
        self.description = description
        self._equation_lambdified = None

    def _initialise_dependencies(
        self, 
        variables: set, 
        parameters: set, 
        warn: bool = True
    ):
        """
        Computes variable/parameter dependencies, i.e. the subsets of
        variables/parameters whose symbols appear as free symbols of self.expression.

        Args:
            variables: variables that self.expression may contain.
            parameters: parameters that equation may contain.
            warn: raise an error if there are symbols not accounted for.

        Raises:
            DependencyError: if `warn == True` and there are symbols in `self.expression` 
                which are not in variables or parameters.
        """
        all_symbols = variables | parameters
        try:
            equation_symbols = self.expression.free_symbols
        except(AttributeError):
            equation_symbols = set()
        if warn and not equation_symbols.issubset(all_symbols):
            undefined_symbols = equation_symbols - all_symbols
            raise DependencyError(
                f"Undefined symbols in expression {self.expression}: "
                f"The following symbols are not part of {all_symbols}: "
                f"{undefined_symbols}"
            )
        equation_variables = equation_symbols.intersection(variables)
        equation_parameters = equation_symbols.intersection(parameters)
        self.variables = equation_variables
        self.parameters = equation_parameters

    def _lambdify(self, modules):
        # Creates a lambdified (numerical) version of self.expression callable with
        # signature (self.variables | self.parameters).
        self._equation_lambdified = lambdify(
            tuple(self.variables | self.parameters),
            self.expression,
            modules=modules,
            cse=True,
        )
    
    def sub_symbols(self, vars_dict: dict, pars_dict: dict):
        """
        Substitute the variables and parameters of `self` according to dictionary mappings.

        Args:
            vars_dict: a dictionary providing mappings between `sympy.Symbol` objects
            pars_dict: a dictionary providing mappings between `sympy.Symbol` objects
        """
        self.variables = {v.subs(vars_dict) for v in self.variables}
        self.parameters = {p.subs(pars_dict) for p in self.parameters}
        self.expression = self.expression.subs(vars_dict | pars_dict)



class SimVariable(Variable):
    """
    A simulation variable. This is an instance of [`Variable`][psymple.variables.Variable] which stores
    a time series of simulation values and an [`UpdateRule`][psymple.variables.UpdateRule] instance.

    Methods:
        set_update_rule: set the update rule of `self` with an `UpdateRule` instance.
        get_readout: get user-readable information about `self`.
    """
    def __init__(self, variable, initial_value = 0):
        """
        Construct a SimVariable instance from a Variable instance.

        Args:
            variable: the variable to construct the simulation variable from
        """
        super().__init__(variable.symbol, variable.description)
        self.update_rule = None
        self.time_series = [initial_value]
        self.buffer = initial_value

    def set_update_rule(self, update_rule):
        """
        Set the update rule of self.

        Args:
            update_rule: update rule to assign.
        """
        self.update_rule = update_rule

    def __repr__(self):
        return f"d/dt {self.symbol} = {self.update_rule.expression}"

    def get_readout(self, time_symbol: Symbol, print_vars_dict: dict = {}, print_pars_dict: dict = {}, type: str = "default"):
        """
        Get a formatted readout of the variable and update rule information of self.

        Args: 
            time_symbol: the symbol used to display the time (independent) variable
            print_vars_dict: a mapping between `sympy.Symbol` objects to use for the readout
            print_pars_dict: a mapping between `sympy.Symbol` objects to use for the readout
            type: the format of the output. By default, this is a string. Specifying `"latex"`
                prouces a `LaTeX`-compilable output.

        """
        print_symbol = print_vars_dict[self.symbol]
        try:
            time_symbol = print_vars_dict[time_symbol]
        except:
            time_symbol = Symbol("T")
        print_equation = self.update_rule.expression.subs(print_vars_dict | print_pars_dict)
        if type == "latex":
            return latex(Eq(Derivative(print_symbol, time_symbol), print_equation), mul_symbol="dot")
        else:
            return f"d{print_symbol}/d{time_symbol} = {print_equation}"
        
    @property
    def initial_value(self):
        return self.time_series[0]
    
    @initial_value.setter
    def initial_value(self, value):
        self.time_series = [value]
        

class SimParameter(Parameter):
    """
    A simulation parameter. This is an instance of [`Parameter`][psymple.variables.Parameter] which stores
    an [`UpdateRule`][psymple.variables.UpdateRule] instance.

    Methods:
        initialise_update_rule
        change_parameter_value
        set_update_rule
        get_readout
    """
    def __init__(self, parameter, type, computed_value=None):
        super().__init__(parameter.symbol, parameter.value, parameter.description)
        # TODO: Redundancy:
        # The value attribute inherited from Parameter is redundant here
        # because it's implicit in the UpdateRule.
        self.computed_value = computed_value
        self.update_rule = None
        self.type=type

    def initialise_update_rule(self, variables, parameters):
        """
        Create the update rule for self from `self.value`.

        Args: 
            variables: a set of variables of which the variables in `self.value` are a subset.
            parameters: a set of parameters of which the parameters in `self.value` are a subset.
        """
        self.update_rule = SimUpdateRule(
            self.value,
            variables,
            parameters,
            f"UpdateRule for {self.symbol} ({self.description})",
        )

    def change_parameter_value(self, new_value: Basic | str | float | int, variables, parameters):
        """
        Change the parameter value. For robustness, `self.value` is updated to the new value,
        and `self.update_rule` is re-initialised.

        Args:
            new_value: the new value to assign.
            variables: a set of symbols of which the variables in `new_value` are a subset.
            parameters: a set of symbols of which the parameters in `new_value` are a subset.
        """
        self.value = new_value
        self.initialise_update_rule(variables, parameters)

    @property
    def dependent_parameters(self):
        return self.update_rule.parameters

    @property
    def expression(self):
        return self.update_rule.expression

    def get_readout(self, print_vars_dict: dict = {}, print_pars_dict: dict = {}, type: str = "default"):
        """
        Get a formatted readout of the variable and update rule information of self.

        Args: 
            print_vars_dict: a mapping between `sympy.Symbol` objects to use for the readout
            print_pars_dict: a mapping between `sympy.Symbol` objects to use for the readout
            type: the format of the output. By default, this is a string. Specifying `"latex"`
                prouces a `LaTeX`-compilable output.

        """
        print_symbol = print_pars_dict[self.symbol]
        try:
            print_equation = self.expression.subs(print_vars_dict | print_pars_dict)
        except AttributeError:
            print_equation = Symbol("REQ")
        if type == "latex":
            return latex(Eq(print_symbol, print_equation), mul_symbol = "dot")
        else:
            return f"{print_symbol} = {print_equation}"


class SimUpdateRule(UpdateRule):
    """
    A convenience class to identify [`UpdateRule`][psymple.variables.UpdateRule] instances 
    which have been instantiated alongside [`UpdateRule`][psymple.variables.UpdateRule] or
    [`UpdateRule`][psymple.variables.UpdateRule] instances.
    """