import sympy as sym

class Parameter:
    def __init__(self, name, symbol_name=None, value=None):
        '''
        Args:
            name (string):
            symbol_name (string):
            value: A numerical value or a sympy expression that may contain a
                time variable T (and maybe spatial information in the future?)
        '''
        self.name = name
        self.symbol = sym.Symbol(symbol_name or name)
        self.value = value

    def reconcile_parameters(main_parameters, new_parameters, warn=False):
        '''
        Update the main_parameters dictionary with new_parameters.

        If one parameter is not None, its value is used.
        Consistency is checked, i.e. we check that the values match if both are
        not None.

        Args:
            main_parameters Dict[str, Parameter]:
                The parameter dictionary to be updated
            new_parameters List[Parameter]:
                The new parameters to update main_parameters with
            warn: if True, only issue warning for parameter mismatch.
        '''
        for param in new_parameters:
            if param.name not in main_parameters:
                main_parameters[param.name] = param
            else:
                # Ensure that the parameter value is consistent with the existing value
                # If the old or new parameter value is not None, use that.
                existing_param = main_parameters[param.name]
                if existing_param.value is not None and param.value is not None:
                    if existing_param.value != param.value:
                        message = f"Value mismatch for parameter {param.name}: {param.value} != {existing_param.value}"
                        if warn:
                            print("Warning: " + message)
                        else:
                            raise ValueError(message)
                if param.value is not None:
                    main_parameters[param.name] = param


class Variable:
    def __init__(self, name, symbol, initial_value):
        self.name = name
        self.initial_value = initial_value
        self.symbol = symbol
