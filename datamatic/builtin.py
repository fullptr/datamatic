"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from . import context


def error_type(typename, obj, expected_type):
    return RuntimeError(f"{obj} is not parsable as '{typename}': Wrong type - expected one of '{expected_type}'")

def error_length(typename, obj, expected_size, actual_size):
    return RuntimeError(f"{obj} is not parsable as '{typename}': Incorrect number of elements for {typename}, got {actual_size}, expected {expected_size}")


def main(ctx: context.Context):

    @ctx.compmethod("name")
    @ctx.attrmethod("name")
    def _(obj):
        return obj["name"]

    @ctx.compmethod("display_name")
    @ctx.attrmethod("display_name")
    def _(obj):
        return obj["display_name"]

    @ctx.attrmethod("type")
    def _(attr):
        return attr["type"]

    @ctx.attrmethod("default")
    def _(attr):
        return attr["default"]

    @ctx.compmethod("if_nth_else")
    def if_nth_else(comp, n, yes_token, no_token):
        try:
            return yes_token if comp == ctx.spec["components"][int(n)] else no_token
        except IndexError:
            return no_token

    @ctx.compmethod("if_first")
    def _(comp, token):
        return if_nth_else(comp, "0", token, "")

    @ctx.compmethod("if_not_first")
    def _(comp, token):
        return if_nth_else(comp, "0", "", token)

    @ctx.compmethod("if_last")
    def _(comp, token):
        return if_nth_else(comp, "-1", token, "")

    @ctx.compmethod("if_not_last")
    def _(comp, token):
        return if_nth_else(comp, "-1", "", token)