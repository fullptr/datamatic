"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""

import type_parse


class Plugin:
    @classmethod
    def get(cls, name):
        for c in cls.__subclasses__():
            if c.__name__ == name:
                return c
        raise RuntimeError(f"Could not find plugin {name}")

    @classmethod
    def get_function(cls, namespace, plugin_name, function_name):
        assert namespace in {"Comp", "Attr"}
        function = getattr(Plugin.get(plugin_name), function_name)
        assert hasattr(function, f"_{namespace}"), f"{function_name} is not in the namespace {namespace}"
        return function


def compmethod(method):
    method._Comp = None
    return classmethod(method)


def attrmethod(method):
    method._Attr = None
    return classmethod(method)


def compattrmethod(method):
    method._Comp = None
    method._Attr = None
    return classmethod(method)


# BUITLIN PLUGINS


class builtin(Plugin):
    """
    The default plugin. When parsing a token to replace, if there are only two parameters,
    this is the assumed plugin. Contains simple accessors and some other helpers.
    """


    # Accessors

    @compattrmethod
    def name(cls, obj):
        return obj["name"]

    @compattrmethod
    def display_name(cls, obj):
        return obj["display_name"]

    @attrmethod
    def type(cls, attr):
        return attr["type"]

    @attrmethod
    def default(cls, attr):
        return type_parse.parse(attr["type"], attr["default"])


    # Conditional helpers

    @compmethod
    def if_nth_else(cls, comp, args, spec):
        [n, yes_token, no_token] = args
        return yes_token if comp == spec["components"][int(n)] else no_token

    @compmethod
    def if_first(cls, comp, args, spec):
        [token] = args
        return cls.if_nth_else(comp, ["0", token, ""], spec)

    @compmethod
    def if_not_first(cls, comp, args, spec):
        [token] = args
        return cls.if_nth_else(comp, ["0", "", token], spec)

    @compmethod
    def if_last(cls, comp, args, spec):
        [token] = args
        return cls.if_nth_else(comp, ["-1", token, ""], spec)

    @compmethod
    def if_not_last(cls, comp, args, spec):
        [token] = args
        return cls.if_nth_else(comp, ["-1", "", token], spec)