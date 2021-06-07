"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
import pathlib
import importlib.util
from functools import partial


class MethodRegister:
    def __init__(self):
        self.methods = {}
    
    def compmethod(self, function_name=None):
        return self.method("Comp", function_name)


    def attrmethod(self, function_name=None):
        return self.method("Attr", function_name)

    def method(self, namespace, function_name=None):
        def decorate(function):
            fn_name = function_name or function.__name__
            if (namespace, fn_name) in self.methods:
                raise RuntimeError(f"An implementation already exists for {namespace}::{fn_name}")
            self.methods[namespace, fn_name] = function
            return function
        return decorate

    def get(self, namespace, function_name):
        if (namespace, function_name) in self.methods:
            return self.methods[namespace, function_name]
        if namespace == "Comp":
            return lambda ctx: ctx.comp[function_name]
        return lambda ctx: ctx.attr[function_name]

    def load_builtins(self):
        """
        A function for loading a bunch of built in custom functions.
        """

        @self.compmethod()
        @self.attrmethod()
        def if_nth_else(ctx, n, yes_token, no_token):
            try:
                if ctx.namespace == "Comp":
                    return yes_token if ctx.comp == ctx.spec[int(n)] else no_token
                return yes_token if ctx.attr == ctx.comp["attributes"][int(n)] else no_token
            except IndexError:
                return no_token

        @self.compmethod()
        @self.attrmethod()
        def if_first(ctx, token):
            return if_nth_else(ctx, "0", token, "")

        @self.compmethod()
        @self.attrmethod()
        def if_not_first(ctx, token):
            return if_nth_else(ctx, "0", "", token)

        @self.compmethod()
        @self.attrmethod()
        def if_last(ctx, token):
            return if_nth_else(ctx, "-1", token, "")

        @self.compmethod()
        @self.attrmethod()
        def if_not_last(ctx, token):
            return if_nth_else(ctx, "-1", "", token)

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