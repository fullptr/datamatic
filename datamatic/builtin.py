"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from .api import Plugin, compmethod, attrmethod, compattrmethod

parse = None  # TODO: Remove this global

def main(type_parser):
    global parse
    assert type_parser is not None
    parse = type_parser
    print("setting parser!")


class Builtin(Plugin):
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
        return parse(attr["type"], attr["default"])

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
