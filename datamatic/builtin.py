"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from contextlib import suppress
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
        return ctx.types.parse(attr["type"], attr["default"])

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

    @ctx.type("int")
    def _(typename, obj) -> str:
        if not isinstance(obj, int):
            raise error_type(typename, obj, int)
        return str(obj)

    @ctx.type("float")
    def _(typename, obj) -> str:
        if not isinstance(obj, (int, float)):
            raise error_type(typename, obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0f"
        return f"{obj}f"

    @ctx.type("double")
    def _(typename, obj) -> str:
        if not isinstance(obj, (int, float)):
            raise error_type(typename, obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0"
        return f"{obj}"

    @ctx.type("bool")
    def _(typename, obj) -> str:
        if not isinstance(obj, bool):
            raise error_type(typename, obj, bool)
        return "true" if obj else "false"

    @ctx.type("std::string")
    def _(typename, obj) -> str:
        if not isinstance(obj, str):
            raise error_type(typename, obj, str)
        return f'"{obj}"'

    @ctx.type("std::vector<{}>")
    @ctx.type("std::deque<{}>")
    @ctx.type("std::queue<{}>")
    @ctx.type("std::stack<{}>")
    @ctx.type("std::list<{}>")
    @ctx.type("std::forward_list<{}>")
    @ctx.type("std::set<{}>")
    @ctx.type("std::unordered_set<{}>")
    @ctx.type("std::multiset<{}>")
    @ctx.type("std::unordered_multiset<{}>")
    def _(typename, subtype, obj) -> str:
        if not isinstance(obj, list):
            raise error_type(typename, obj, list)
        rep = ", ".join(ctx.types.parse(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"

    @ctx.type("std::array<{}, {}>")
    def _(typename, subtype, size, obj) -> str:
        if not isinstance(obj, list):
            raise error_type(typename, obj, list)
        if not size.isdigit():
            raise RuntimeError(f"Second parameter to std::array must be an integer, got '{size}'")
        if len(obj) != int(size):
            raise error_length(typename, obj, size, len(obj))
        rep = ", ".join(ctx.types.parse(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"

    @ctx.type("std::pair<{}, {}>")
    def _(typename, firsttype, secondtype, obj) -> str:
        if not isinstance(obj, list):
            raise error_type(typename, obj, list)
        if len(obj) != 2:
            raise error_length(typename, obj, 2, len(obj))
        firstraw, secondraw = obj
        first = ctx.types.parse(firsttype, firstraw)
        second = ctx.types.parse(secondtype, secondraw)
        return f"{typename}{{{first}, {second}}}"

    @ctx.type("std::map<{}, {}>")
    @ctx.type("std::unordered_map<{}, {}>")
    @ctx.type("std::multimap<{}, {}>")
    @ctx.type("std::unordered_multimap<{}, {}>")
    def _(typename, keytype, valuetype, obj) -> str:
        if isinstance(obj, list):
            pairs = obj
        elif isinstance(obj, dict):
            pairs = obj.items()
        else:
            raise error_type(typename, obj, (list, dict))

        rep = ", ".join(f"{{{ctx.types.parse(keytype, k)}, {ctx.types.parse(valuetype, v)}}}" for k, v in pairs)
        return f"{typename}{{{rep}}}"

    @ctx.type("std::optional<{}>")
    def _(typename, subtype, obj) -> str:
        if obj is not None:
            rep = ctx.types.parse(subtype, obj)
            return f"{typename}{{{rep}}}"
        else:
            return "std::nullopt"

    @ctx.type("std::unique_ptr<{}>", make_fn="std::make_unique")
    @ctx.type("std::shared_ptr<{}>", make_fn="std::make_shared")
    def _(typename, subtype, obj, make_fn) -> str:
        if obj is not None:
            return f"{make_fn}<{subtype}>({ctx.types.parse(subtype, obj)})"
        return "nullptr"

    @ctx.type("std::weak_ptr<{}>")
    def _(typename, subtype, obj) -> str:
        assert obj is None
        return "nullptr"

    @ctx.type("std::any")
    @ctx.type("std::monostate")
    def _(typename, obj) -> str:
        assert obj is None
        return f"{typename}{{}}"

    @ctx.type("std::tuple<{}...>")
    def _(typename, subtypes, obj) -> str:
        if not isinstance(obj, list):
            raise error_type(typename, obj, list)
        if len(obj) != len(subtypes):
            raise error_length(typename, obj, len(subtypes), len(obj))
        rep = ", ".join(ctx.types.parse(subtype, val) for subtype, val in zip(subtypes, obj))
        return f"{typename}{{{rep}}}"

    @ctx.type("std::variant<{}...>")
    def _(typename, subtypes, obj) -> str:
        for subtype in subtypes:
            with suppress(Exception):
                return ctx.types.parse(subtype, obj)
        raise error_type(typename, obj, list)

    @ctx.type("std::function<{}({})>")
    def _(typename, returntype, argtype, obj) -> str:
        if not isinstance(obj, str):
            raise error_type(typename, obj, str) # We cannot parse a lambda, so just assume the given value is good
        return obj
