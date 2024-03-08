from abc import ABC, abstractmethod

import sympy as sym

from psymple.globals import sym_custom_ns


class DependencyError(Exception):
    pass


class SymbolWrapper:
    def __init__(self, symbol: sym.Symbol, description: str = ""):
        if type(symbol) is str:
            symbol = sym.Symbol(symbol)
        self.symbol = symbol
        self.description = description

    @property
    def name(self):
        return str(self.symbol)

    def __repr__(self):
        return f"{type(self).__name__} object: {self.symbol} ({self.description})"


class Container(ABC):
    @abstractmethod
    def __init__(self, objects):
        if objects is None:
            objects = []
        # TODO: check for duplicates in objects on creation
        self.objects = objects
        # self.contains_type = SymbolWrapper

    def __add__(self, other):
        if isinstance(other, type(self)):
            to_add = other.objects
        elif isinstance(other, self.contains_type):
            to_add = [other]
        else:
            raise TypeError(f"Unsupported addition type within {type(self)}.__name__")
        for obj in to_add:
            if self.check_duplicates:
                self._duplicates(self.get_symbols(), obj.symbol)
        return type(self)(self.objects + to_add)

    # TODO: We should define __iter__().

    def __len__(self):
        return len(self.objects)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(self.objects[index])
        elif isinstance(index, int):
            return self.objects[index]
        elif isinstance(index, (str, sym.Symbol)):
            return self._objectify(index)

    def __contains__(self, item):
        try:
            self[item]
        except StopIteration:
            return False
        return True

    def _duplicates(self, list, object):
        if object in list:
            raise Exception(
                f"The symbol '{object}' has already been defined. Try a new symbol."
            )

    def _edit(self, edit_type, index=None, object=None):
        if edit_type == "remove":
            del self.objects[index]
        elif edit_type == "replace":
            self._duplicates(self.objects, object)
            self[index] = object
        elif edit_type == "add":
            self._duplicates(self.objects, object)
            self.objects += [object]

    def _objectify(self, expr):
        if isinstance(expr, str) or isinstance(expr, sym.Symbol):
            return next(
                obj
                for obj in self.objects
                if obj.symbol == sym.sympify(expr, locals=sym_custom_ns)
            )
        elif isinstance(expr, self.contains_type):
            return expr
        else:
            raise TypeError(
                f"arguments to _objectify should be of type {repr(str)}, "
                f"{repr(sym.Symbol)} or {self.contains_type}"
            )

    def __repr__(self):
        return "[" + ", ".join([str(obj) for obj in self.objects]) + "]"
