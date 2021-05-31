"""
The Builtin plugin which contains "attribute access" and some helpful functions.
"""
from contextlib import suppress
from . import api

def main(type_parser: api.TypeParser, plugin_list: api.PluginList):

    @type_parser.register("int")
    def _(typename, obj) -> str:
        assert isinstance(obj, int)
        return str(obj)


    @type_parser.register("float")
    def _(typename, obj) -> str:
        assert isinstance(obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0f"
        return f"{obj}f"


    @type_parser.register("double")
    def _(typename, obj) -> str:
        assert isinstance(obj, (int, float))
        if "." not in str(obj):
            return f"{obj}.0"
        return f"{obj}"


    @type_parser.register("bool")
    def _(typename, obj) -> str:
        assert isinstance(obj, bool)
        return "true" if obj else "false"


    @type_parser.register("std::string")
    def _(typename, obj) -> str:
        assert isinstance(obj, str)
        return f'"{obj}"'


    @type_parser.register("std::vector<{}>")
    @type_parser.register("std::deque<{}>")
    @type_parser.register("std::queue<{}>")
    @type_parser.register("std::stack<{}>")
    @type_parser.register("std::list<{}>")
    @type_parser.register("std::forward_list<{}>")
    @type_parser.register("std::set<{}>")
    @type_parser.register("std::unordered_set<{}>")
    @type_parser.register("std::multiset<{}>")
    @type_parser.register("std::unordered_multiset<{}>")
    def _(typename, subtype, obj) -> str:
        assert isinstance(obj, list)
        rep = ", ".join(type_parser(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"


    @type_parser.register("std::array<{}, {}>")
    def _(typename, subtype, size, obj) -> str:
        assert size.isdigit(), f"Second parameter to std::array must be an integer, got '{size}'"
        assert isinstance(obj, list), f"std::array expects a list of elements, got '{obj}'"
        assert len(obj) == int(size), f"Incorrect number of elements for std::array, got {len(obj)}, expected {size}"
        rep = ", ".join(type_parser(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"


    @type_parser.register("std::pair<{}, {}>")
    def _(typename, firsttype, secondtype, obj) -> str:
        assert isinstance(obj, list)
        assert len(obj) == 2
        firstraw, secondraw = obj
        first = type_parser(firsttype, firstraw)
        second = type_parser(secondtype, secondraw)
        return f"{typename}{{{first}, {second}}}"


    @type_parser.register("std::map<{}, {}>")
    @type_parser.register("std::unordered_map<{}, {}>")
    @type_parser.register("std::multimap<{}, {}>")
    @type_parser.register("std::unordered_multimap<{}, {}>")
    def _(typename, keytype, valuetype, obj) -> str:
        if isinstance(obj, list):
            pairs = obj
        elif isinstance(obj, dict):
            pairs = obj.items()
        else:
            raise RuntimeError(f"Could not parse {obj} as {typename}")

        rep = ", ".join(f"{{{type_parser(keytype, k)}, {type_parser(valuetype, v)}}}" for k, v in pairs)
        return f"{typename}{{{rep}}}"


    @type_parser.register("std::optional<{}>")
    def _(typename, subtype, obj) -> str:
        if obj is not None:
            rep = type_parser(subtype, obj)
            return f"{typename}{{{rep}}}"
        else:
            return "std::nullopt"


    @type_parser.register("std::unique_ptr<{}>", make_fn="std::make_unique")
    @type_parser.register("std::shared_ptr<{}>", make_fn="std::make_shared")
    def _(typename, subtype, obj, make_fn) -> str:
        if obj is not None:
            return f"{make_fn}<{subtype}>({type_parser(subtype, obj)})"
        return "nullptr"


    @type_parser.register("std::weak_ptr<{}>")
    def _(typename, subtype, obj) -> str:
        assert obj is None
        return "nullptr"


    @type_parser.register("std::any")
    @type_parser.register("std::monostate")
    def _(typename, obj) -> str:
        assert obj is None
        return f"{typename}{{}}"


    @type_parser.register("std::tuple<{}...>")
    def _(typename, subtypes, obj) -> str:
        assert isinstance(obj, list)
        assert len(subtypes) == len(obj)
        rep = ", ".join(parse(subtype, val) for subtype, val in zip(subtypes, obj))
        return f"{typename}{{{rep}}}"


    @type_parser.register("std::variant<{}...>")
    def _(typename, subtypes, obj) -> str:
        for subtype in subtypes:
            with suppress(Exception):
                return parse(subtype, obj)
        raise RuntimeError(f"{obj} cannot be parsed into any of {subtypes}")


    @type_parser.register("std::function<{}({})>")
    def _(typename, returntype, argtype, obj) -> str:
        assert isinstance(obj, str) # We cannot parse a lambda, so just assume the given value is good
        return obj


    @plugin_list.compattrmethod("Builtin", "name")
    def _(obj):
        return obj["name"]

    @plugin_list.compattrmethod("Builtin", "display_name")
    def _(obj):
        return obj["display_name"]

    @plugin_list.attrmethod("Builtin", "type")
    def _(attr):
        return attr["type"]

    @plugin_list.attrmethod("Builtin", "default")
    def _(attr):
        return type_parser(attr["type"], attr["default"])

    @plugin_list.compmethod("Builtin", "if_nth_else")
    def if_nth_else(comp, args, spec):
        [n, yes_token, no_token] = args
        return yes_token if comp == spec["components"][int(n)] else no_token

    @plugin_list.compmethod("Builtin", "if_first")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["0", token, ""], spec)

    @plugin_list.compmethod("Builtin", "if_not_first")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["0", "", token], spec)

    @plugin_list.compmethod("Builtin", "if_last")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["-1", token, ""], spec)

    @plugin_list.compmethod("Builtin", "if_not_last")
    def _(comp, args, spec):
        [token] = args
        return if_nth_else(comp, ["-1", "", token], spec)
