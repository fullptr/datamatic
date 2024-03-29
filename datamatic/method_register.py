"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
import pathlib
import importlib.util
from functools import partialmethod

from . import utilities


class MethodRegister:
    def __init__(self):
        self.methods = {}

    def register_method(self, function, namespace):
        fn_name = function.__name__
        if (namespace, fn_name) in self.methods:
            raise RuntimeError(f"An implementation already exists for {namespace}::{fn_name}")
        self.methods[namespace, fn_name] = function
        return function

    compmethod = partialmethod(register_method, namespace="Comp")
    attrmethod = partialmethod(register_method, namespace="Attr")
    globalmethod = partialmethod(register_method, namespace="Global")

    def get(self, namespace, function_name):
        if (namespace, function_name) in self.methods:
            return self.methods[namespace, function_name]
        if namespace == "Global":
            return lambda ctx: ctx.spec[function_name]
        if namespace == "Comp":
            return lambda ctx: ctx.comp[function_name]
        return lambda ctx: ctx.attr[function_name]

    def load_builtins(self):
        """
        A function for loading a bunch of built in custom functions.
        """

        @self.compmethod
        @self.attrmethod
        def if_nth_else(ctx, n: int, yes_token: str, no_token:str) -> str:
            try:
                if ctx.namespace == "Comp":
                    comps = utilities.filter_flags(ctx.spec["components"], ctx.flags)
                    return yes_token if ctx.comp == comps[n] else no_token
                attrs = utilities.filter_flags(ctx.comp["attributes"], ctx.flags)
                return yes_token if ctx.attr == attrs[n] else no_token
            except IndexError:
                return no_token

        @self.compmethod
        @self.attrmethod
        def if_first(ctx, token):
            return if_nth_else(ctx, 0, token, "")

        @self.compmethod
        @self.attrmethod
        def if_not_first(ctx, token):
            return if_nth_else(ctx, 0, "", token)

        @self.compmethod
        @self.attrmethod
        def if_last(ctx, token):
            return if_nth_else(ctx, -1, token, "")

        @self.compmethod
        @self.attrmethod
        def if_not_last(ctx, token):
            return if_nth_else(ctx, -1, "", token)

        @self.compmethod
        def attr_count(ctx):
            attrs = utilities.filter_flags(ctx.comp["attributes"], ctx.flags)
            return str(len(attrs))

        @self.compmethod
        def attr_list(ctx, field, separator, format="{}"):
            attrs = utilities.filter_flags(ctx.comp["attributes"], ctx.flags)
            return separator.join(format.format(attr[field]) for attr in attrs)

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
