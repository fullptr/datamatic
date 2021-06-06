"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
import pathlib
import importlib.util


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

    def load_builtins(self):
        """
        A function for loading a bunch of built in custom functions.
        """

        @self.compmethod("if_nth_else")
        def if_nth_else(spec, comp, n, yes_token, no_token):
            try:
                return yes_token if comp == spec[int(n)] else no_token
            except IndexError:
                return no_token

        @self.compmethod("if_first")
        def _(spec, comp, token):
            return if_nth_else(spec, comp, "0", token, "")

        @self.compmethod("if_not_first")
        def _(spec, comp, token):
            return if_nth_else(spec, comp, "0", "", token)

        @self.compmethod("if_last")
        def _(spec, comp, token):
            return if_nth_else(spec, comp, "-1", token, "")

        @self.compmethod("if_not_last")
        def _(spec, comp, token):
            return if_nth_else(spec, comp, "-1", "", token)

    def load_from_dmx(self, directory: pathlib.Path):
        """
        A function that scans the given directory for dmx files, and runs the
        main function in each to load up custom functions.
        """
        for file in directory.glob("**/*.dmx.py"):
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main(self)