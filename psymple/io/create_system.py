import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from psymple.build import (
    FunctionalPortedObject,
    VariablePortedObject,
    CompositePortedObject,
)

PORTED_OBJECTS = {
    "functional": FunctionalPortedObject,
    "variable": VariablePortedObject,
    "compsite": CompositePortedObject,
}

ALIASES = {
    "functional": [
        "fpo",
        "functional ported object",
        "functional_ported_object",
        "functional object",
        "functional_object",
    ],
    "variable": [
        "vpo",
        "variable ported object",
        "variable_ported_object",
        "variable object",
        "variable_object",
    ],
    "composite": [
        "cpo",
        "composite ported object",
        "composite_ported_object",
        "composite object",
        "composite_object"
    ]
}


class System_Creator:
    def __init__(self):
        self.ported_objects = {}

    @classmethod
    def from_json(cls, file):
        data = json.loads(file)
        return cls(data)

    def _process(self, data: dict, sympify_locals = {}):
        for key in data.keys():
            obj_data = data[key]
            obj_type = obj_data.pop("type")
            obj_data.update({"name": key})
            if obj_type in ALIASES["functional"]:  
                obj = self._build_functional_object(obj_data, sympify_locals)
            elif obj_type in ALIASES["variable"]:
                obj = self._build_variable_object(obj_data, sympify_locals)
            elif obj_type in ALIASES["composite"]:
                obj = self._build_composite_object(obj_data)
            else:
                raise KeyError(f"{obj_type} is not a recognised type for object {key}")
            self.ported_objects[key] = obj


    def _build_functional_object(self, data, sympify_locals):
        print(sympify_locals)
        return FunctionalPortedObject(**data, sympify_locals=sympify_locals)

    def _build_variable_object(self, data, sympify_locals):
        return VariablePortedObject(**data, sympify_locals=sympify_locals)
    
    def _build_composite_object(self, data):
        if isinstance(data["children"], list):
            children = [self.ported_objects[obj] for obj in data["children"]]
            data["children"] = children
            return CompositePortedObject(**data)
        elif isinstance(data["children"], dict):
            raise NotImplementedError("This has not been implemented yet.")
        
    def get_system(self, system: str = None):
        """
        Returns the object from self.ported_objects stored by the string system, or
        if not provided the last object to be added.
        """
        if system:
            ret = self.ported_objects[system]
        else:
            ret = self.ported_objects.popitem()[1]
        return ret
         