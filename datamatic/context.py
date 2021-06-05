"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""


class MethodRegister:
    def __init__(self):
        self.methods = {}
    
    def compmethod(self, function_name):
        return self.method("Comp", function_name)

    def attrmethod(self, function_name):
        return self.method("Attr", function_name)

    def method(self, namespace, function_name):
        def decorate(function):
            if (namespace, function_name) in self.methods:
                raise RuntimeError(f"An implementation already exists for {namespace}::{function_name}")
            self.methods[namespace, function_name] = function
            return function
        return decorate

    def get(self, namespace, function_name):
        if (namespace, function_name) in self.methods:
            return self.methods[namespace, function_name]
        return lambda _, obj: obj[function_name]