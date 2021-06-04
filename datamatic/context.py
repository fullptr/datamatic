"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
import functools
import parse


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


class TypeParser:
    def __init__(self):
        self.dispatchers = {}
        self.template_dispatchers = {}
        self.variadic_dispatchers = {}

    def register(self, first, **kwargs):
        def decorator(func):
            if "{}..." in first:
                if first.count("{}") != 1:
                    raise RuntimeError("Variadic and non-variadic mixing not supported")
                newfirst = first.replace("{}...", "{}")
                if newfirst in self.variadic_dispatchers:
                    raise RuntimeError(f"'{newfirst}' already has a registered parser")
                self.variadic_dispatchers[newfirst] = functools.partial(func, **kwargs)
            elif "{}" in first:
                if first in self.template_dispatchers:
                    raise RuntimeError(f"'{first}' already has a registered parser")
                self.template_dispatchers[first] = functools.partial(func, **kwargs)
            else:
                if first in self.dispatchers:
                    raise RuntimeError(f"'{first}' already has a registered parser")
                self.dispatchers[first] = functools.partial(func, **kwargs)
            return func
        return decorator

    def parse(self, first, *args, **kwargs):
        if first in self.dispatchers:
            return self.dispatchers[first](first, *args, **kwargs)

        for key, value in self.template_dispatchers.items():
            if result := parse.parse(key, first):
                types = list(result)
                return value(first, *types, *args, **kwargs)

        for key, value in self.variadic_dispatchers.items():
            if result := parse.parse(key, first):
                types = parse_variadic_typelist(result[0])
                return value(first, types, *args, **kwargs)

        raise RuntimeError(f"No parser registered for '{first}'")

class Context:
    def __init__(self, spec):
        self.spec = spec
        self.methods = {}
        self.types = TypeParser()
    
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

    def type(self, *args, **kwargs):
        return self.types.register(*args, **kwargs)

    def parse(self, *args, **kwargs):
        return self.types.parse(*args, **kwargs)

    def get(self, namespace, function_name):
        if (namespace, function_name) in self.methods:
            return self.methods[namespace, function_name]
        raise RuntimeError(f"Could not find {namespace}.{function_name}")