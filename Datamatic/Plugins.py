"""
A module that holds Plugin, a base class for plugins to Datamatic.
Users can implement plugins that hook up to tokens in dm files for
custom behaviour.
"""
from Datamatic import Types


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
    @compattrmethod
    def Name(cls, comp):
        return comp["Name"]

    @compattrmethod
    def DisplayName(cls, comp):
        return comp["DisplayName"]

    @attrmethod
    def Type(cls, attr):
        return attr["Type"]

    @attrmethod
    def Default(cls, attr):
        cls = Types.get(attr["Type"])
        return repr(cls(attr["Default"]))


class conditional(Plugin):
    @compmethod
    def if_nth_else(cls, comp, args, spec):
        [n, yes_token, no_token] = args
        return yes_token if comp == spec["Components"][int(n)] else no_token

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