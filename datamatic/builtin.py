"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from . import context


def main(methods: context.MethodRegister):

    @methods.compmethod("if_nth_else")
    def if_nth_else(spec, comp, n, yes_token, no_token):
        try:
            return yes_token if comp == spec[int(n)] else no_token
        except IndexError:
            return no_token

    @methods.compmethod("if_first")
    def _(spec, comp, token):
        return if_nth_else(spec, comp, "0", token, "")

    @methods.compmethod("if_not_first")
    def _(spec, comp, token):
        return if_nth_else(spec, comp, "0", "", token)

    @methods.compmethod("if_last")
    def _(spec, comp, token):
        return if_nth_else(spec, comp, "-1", token, "")

    @methods.compmethod("if_not_last")
    def _(spec, comp, token):
        return if_nth_else(spec, comp, "-1", "", token)