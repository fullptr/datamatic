"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from contextlib import suppress
from . import api

def main(context: api.Context):

    @context.types.register("int")
    def _(typename, obj) -> str:
        assert isinstance(obj, int)
        return str(obj)


    @context.types.register("float")
    def _(typename, obj) -> str:
        assert isinstance(obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0f"
        return f"{obj}f"


    @context.types.register("double")
    def _(typename, obj) -> str:
        assert isinstance(obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0"
        return f"{obj}"


    @context.types.register("bool")
    def _(typename, obj) -> str:
        assert isinstance(obj, bool)
        return "true" if obj else "false"


    @context.types.register("std::string")
    def _(typename, obj) -> str:
        assert isinstance(obj, str)
        return f'"{obj}"'


    @context.types.register("std::vector<{}>")
    @context.types.register("std::deque<{}>")
    @context.types.register("std::queue<{}>")
    @context.types.register("std::stack<{}>")
    @context.types.register("std::list<{}>")
    @context.types.register("std::forward_list<{}>")
    @context.types.register("std::set<{}>")
    @context.types.register("std::unordered_set<{}>")
    @context.types.register("std::multiset<{}>")
    @context.types.register("std::unordered_multiset<{}>")
    def _(typename, subtype, obj) -> str:
        assert isinstance(obj, list)
        rep = ", ".join(context.types.parse(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"


    @context.types.register("std::array<{}, {}>")
    def _(typename, subtype, size, obj) -> str:
        assert size.isdigit(), f"Second parameter to std::array must be an integer, got '{size}'"
        assert isinstance(obj, list), f"std::array expects a list of elements, got '{obj}'"
        assert len(obj) == int(size), f"Incorrect number of elements for std::array, got {len(obj)}, expected {size}"
        rep = ", ".join(context.types.parse(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"


    @context.types.register("std::pair<{}, {}>")
    def _(typename, firsttype, secondtype, obj) -> str:
        assert isinstance(obj, list)
        assert len(obj) == 2
        firstraw, secondraw = obj
        first = context.types.parse(firsttype, firstraw)
        second = context.types.parse(secondtype, secondraw)
        return f"{typename}{{{first}, {second}}}"


    @context.types.register("std::map<{}, {}>")
    @context.types.register("std::unordered_map<{}, {}>")
    @context.types.register("std::multimap<{}, {}>")
    @context.types.register("std::unordered_multimap<{}, {}>")
    def _(typename, keytype, valuetype, obj) -> str:
        if isinstance(obj, list):
            pairs = obj
        elif isinstance(obj, dict):
            pairs = obj.items()
        else:
            raise RuntimeError(f"Could not parse {obj} as {typename}")

        rep = ", ".join(f"{{{context.types.parse(keytype, k)}, {context.types.parse(valuetype, v)}}}" for k, v in pairs)
        return f"{typename}{{{rep}}}"


    @context.types.register("std::optional<{}>")
    def _(typename, subtype, obj) -> str:
        if obj is not None:
            rep = context.types.parse(subtype, obj)
            return f"{typename}{{{rep}}}"
        else:
            return "std::nullopt"


    @context.types.register("std::unique_ptr<{}>", make_fn="std::make_unique")
    @context.types.register("std::shared_ptr<{}>", make_fn="std::make_shared")
    def _(typename, subtype, obj, make_fn) -> str:
        if obj is not None:
            return f"{make_fn}<{subtype}>({context.types.parse(subtype, obj)})"
        return "nullptr"


    @context.types.register("std::weak_ptr<{}>")
    def _(typename, subtype, obj) -> str:
        assert obj is None
        return "nullptr"


    @context.types.register("std::any")
    @context.types.register("std::monostate")
    def _(typename, obj) -> str:
        assert obj is None
        return f"{typename}{{}}"


    @context.types.register("std::tuple<{}...>")
    def _(typename, subtypes, obj) -> str:
        assert isinstance(obj, list)
        assert len(subtypes) == len(obj)
        rep = ", ".join(context.types.parse(subtype, val) for subtype, val in zip(subtypes, obj))
        return f"{typename}{{{rep}}}"


    @context.types.register("std::variant<{}...>")
    def _(typename, subtypes, obj) -> str:
        for subtype in subtypes:
            with suppress(Exception):
                return context.types.parse(subtype, obj)
        raise RuntimeError(f"{obj} cannot be parsed into any of {subtypes}")


    @context.types.register("std::function<{}({})>")
    def _(typename, returntype, argtype, obj) -> str:
        assert isinstance(obj, str) # We cannot parse a lambda, so just assume the given value is good
        return obj


    @context.compattrmethod("Builtin", "name")
    def _(obj):
        return obj["name"]

    @context.compattrmethod("Builtin", "display_name")
    def _(obj):
        return obj["display_name"]

    @context.attrmethod("Builtin", "type")
    def _(attr):
        return attr["type"]

    @context.attrmethod("Builtin", "default")
    def _(attr):
        return context.types.parse(attr["type"], attr["default"])

    @context.compmethod("Builtin", "if_nth_else")
    def if_nth_else(comp, args, spec):
        [n, yes_token, no_token] = args
        return yes_token if comp == spec["components"][int(n)] else no_token

    @context.compmethod("Builtin", "if_first")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["0", token, ""], spec)

    @context.compmethod("Builtin", "if_not_first")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["0", "", token], spec)

    @context.compmethod("Builtin", "if_last")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["-1", token, ""], spec)

    @context.compmethod("Builtin", "if_not_last")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["-1", "", token], spec)
