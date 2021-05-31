"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
import functools
from contextlib import suppress
import parse as _parse


__all__ = ["Plugin", "compmethod", "attrmethod", "compattrmethod", "parse"]


def parse_variadic_typelist(string):
    tokens = []
    current = ""
    stack = []
    open_brackets = "(", "[", "<", "{"
    close_brackets = ")", "]", ">", "}"
    brackets = dict(zip(close_brackets, open_brackets))
    for c in string:
        if c in open_brackets:
            stack.append(c)
        elif c in close_brackets:
            if len(stack) > 0 and stack[-1] == brackets[c]:
                stack.pop()
            else:
                raise RuntimeError(f"Invalid type list '{string}'")
        elif c == "," and stack == []:
            tokens.append(current.strip())
            current = ""
            continue
        current += c

    if len(current) > 0:
        tokens.append(current.strip()) # Append last type
    if stack != []:
        raise RuntimeError(f"Invalid type list '{string}'")
    return tokens


class Context:
    def __init__(self):
        # Plugin Functions
        self.compmethods = {}
        self.attrmethods = {}
        self.compattrmethods = {}

        # Type Parsers
        self.dispatchers = {}
        self.template_dispatchers = {}
        self.variadic_dispatchers = {}

    def compmethod(self, plugin, name):
        def decorate(function):
            self.compmethods["Comp", plugin, name] = function
            return function
        return decorate

    def attrmethod(self, plugin, name):
        def decorate(function):
            self.attrmethods["Attr", plugin, name] = function
            return function
        return decorate

    def compattrmethod(self, plugin, name):
        def decorate(function):
            self.compmethods["Comp", plugin, name] = function
            self.attrmethods["Attr", plugin, name] = function
            return function
        return decorate

    def get(self, namespace, plugin, name):
        if (namespace, plugin, name) in self.compmethods:
            return self.compmethods[namespace, plugin, name]

        if (namespace, plugin, name) in self.attrmethods:
            return self.attrmethods[namespace, plugin, name]

        if (namespace, plugin, name) in self.compattrmethods:
            return self.compattrmethods[namespace, plugin, name]

        raise RuntimeError(f"Could not find {namespace}.{plugin}.{name}")


    def __call__(self, first, *args, **kwargs):
        if first in self.dispatchers:
            return self.dispatchers[first](first, *args, **kwargs)

        for key, value in self.template_dispatchers.items():
            result = _parse.parse(key, first)
            if result is not None:
                types = list(result)
                return value(first, *types, *args, **kwargs)

        for key, value in self.variadic_dispatchers.items():
            result = _parse.parse(key, first)
            if result is not None:
                types = parse_variadic_typelist(result[0])
                return value(first, types, *args, **kwargs)

        raise RuntimeError(f"No parser registered for '{first}'")

    def register(self, first, **kwargs):
        def decorator(func):
            if "{}..." in first:
                assert first.count("{}") == 1, "Variadic and non-variadic mixing not supported"
                newfirst = first.replace("{}...", "{}")
                assert newfirst not in self.variadic_dispatchers, f"'{newfirst}' already has a registered parser"
                self.variadic_dispatchers[newfirst] = functools.partial(func, **kwargs)
            elif "{}" in first:
                assert first not in self.template_dispatchers, f"'{first}' already has a registered parser"
                self.template_dispatchers[first] = functools.partial(func, **kwargs)
            else:
                assert first not in self.dispatchers, f"'{first}' already has a registered parser"
                self.dispatchers[first] = functools.partial(func, **kwargs)
            return func
        return decorator