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

    tokens.append(current.strip()) # Append last type
    if stack != []:
        raise RuntimeError(f"Invalid type list '{string}'")
    return tokens


class SingleDispatch:
    """
    A decorator class designed to implement single dispatch on the first argument of a function.
    """
    def __init__(self, func):
        self.func = func
        self.dispatchers = {}
        self.template_dispatchers = {}
        self.variadic_dispatchers = {}

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

        return self.func(first, *args, **kwargs)

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


@SingleDispatch
def parse(typename, obj) -> str:
    """
    Parse the given object as the given type. A KeyError is raised if there is no
    parser registered for the given type.
    """
    raise RuntimeError(f"No parser registered for '{typename}'")


@parse.register("int")
def _(typename, obj) -> str:
    assert isinstance(obj, int)
    return str(obj)


@parse.register("float")
def _(typename, obj) -> str:
    assert isinstance(obj, (int, float))
    if "." not in str(obj):
        return f"{obj}.0f"
    return f"{obj}f"


@parse.register("double")
def _(typename, obj) -> str:
    assert isinstance(obj, (int, float))
    if "." not in str(obj):
        return f"{obj}.0"
    return f"{obj}"


@parse.register("bool")
def _(typename, obj) -> str:
    assert isinstance(obj, bool)
    return "true" if obj else "false"


@parse.register("std::string")
def _(typename, obj) -> str:
    assert isinstance(obj, str)
    return f'"{obj}"'


@parse.register("std::vector<{}>")
@parse.register("std::deque<{}>")
@parse.register("std::queue<{}>")
@parse.register("std::stack<{}>")
@parse.register("std::list<{}>")
@parse.register("std::forward_list<{}>")
@parse.register("std::set<{}>")
@parse.register("std::unordered_set<{}>")
@parse.register("std::multiset<{}>")
@parse.register("std::unordered_multiset<{}>")
def _(typename, subtype, obj) -> str:
    assert isinstance(obj, list)
    rep = ", ".join(parse(subtype, x) for x in obj)
    return f"{typename}{{{rep}}}"


@parse.register("std::array<{}, {}>")
def _(typename, subtype, size, obj) -> str:
    assert size.isdigit(), f"Second parameter to std::array must be an integer, got '{size}'"
    assert isinstance(obj, list), f"std::array expects a list of elements, got '{obj}'"
    assert len(obj) == int(size), f"Incorrect number of elements for std::array, got {len(obj)}, expected {size}"
    rep = ", ".join(parse(subtype, x) for x in obj)
    return f"{typename}{{{rep}}}"


@parse.register("std::pair<{}, {}>")
def _(typename, firsttype, secondtype, obj) -> str:
    assert isinstance(obj, list)
    assert len(obj) == 2
    firstraw, secondraw = obj
    first = parse(firsttype, firstraw)
    second = parse(secondtype, secondraw)
    return f"{typename}{{{first}, {second}}}"


@parse.register("std::map<{}, {}>")
@parse.register("std::unordered_map<{}, {}>")
@parse.register("std::multimap<{}, {}>")
@parse.register("std::unordered_multimap<{}, {}>")
def _(typename, keytype, valuetype, obj) -> str:
    if isinstance(obj, list):
        pairs = obj
    elif isinstance(obj, dict):
        pairs = obj.items()
    else:
        raise RuntimeError(f"Could not parse {obj} as {typename}")

    rep = "' ".join(f"{{{parse(keytype, k)}, {parse(valuetype, v)}}}" for k, v in pairs)
    return f"{typename}{{{rep}}}"


@parse.register("std::optional<{}>")
def _(typename, subtype, obj) -> str:
    if obj is not None:
        rep = parse(subtype, obj)
        return f"{typename}{{{rep}}}"
    else:
        return "std::nullopt"


@parse.register("std::unique_ptr<{}>", make_fn="std::make_unique")
@parse.register("std::shared_ptr<{}>", make_fn="std::make_shared")
def _(typename, subtype, obj, make_fn) -> str:
    if obj is not None:
        return f"{make_fn}<{subtype}>{{{parse(subtype, obj)}}}"
    return "nullptr"


@parse.register("std::weak_ptr<{}>")
def _(typename, subtype, obj) -> str:
    assert obj is None
    return "nullptr"


@parse.register("std::any")
def _(typename, obj) -> str:
    return f"{typename}{{}}"


@parse.register("std::tuple<{}...>")
def _(typename, subtypes, obj) -> str:
    assert isinstance(obj, list)
    assert len(subtypes) == len(obj)
    rep = ", ".join(parse(subtype, val) for subtype, val in zip(subtypes, obj))
    return f"{typename}{{{rep}}}"


@parse.register("std::monostate")
def _(typename, obj) -> str:
    assert obj is None
    return f"{typename}{{}}"


@parse.register("std::variant<{}...>")
def _(typename, subtypes, obj) -> str:
    for subtype in subtypes:
        with suppress(Exception):
            return parse(subtype, obj)
    raise RuntimeError(f"{obj} cannot be parsed into any of {subtypes}")


@parse.register("std::function<{}({})>")
def _(typename, returntype, argtype, obj) -> str:
    assert isinstance(obj, str) # We cannot parse a lambda, so just assume the given value is good
    return obj


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
