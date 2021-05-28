"""
A module that holds CppType, a base class for classes that represent
C++ types. Users can subclass this to add their own types to
Datamatic.
"""
import functools
import parse as _parse


class Dispatcher:
    """
    A decorator class designed to implement single dispatch on the first argument of a function.
    """
    def __init__(self, func):
        self.func = func
        self.dispatchers = {}
        self.template_dispatchers = {}

    def __call__(self, first, *args, **kwargs):
        if first in self.dispatchers:
            return self.dispatchers[first](first, *args, **kwargs)

        for key, value in self.template_dispatchers.items():
            result = _parse.parse(key, first)
            if result is not None:
                types = list(result)
                return value(first, *types, *args, **kwargs)

        return self.func(first, *args, **kwargs)

    def register(self, first, **kwargs):
        def decorator(func):
            if "{}" in first:
                assert first not in self.template_dispatchers, f"'{first}' already has a registered parser"
                self.template_dispatchers[first] = functools.partial(func, **kwargs)
            else:
                assert first not in self.dispatchers, f"'{first}' already has a registered parser"
                self.dispatchers[first] = functools.partial(func, **kwargs)
            return func
        return decorator


@Dispatcher
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
    assert len(list) == 2
    firstraw, secondraw = list
    first = parse(firsttype, firstraw)
    second = parse(secondtype, secondraw)
    return f"{typename}{{{first}, {second}}}"


@parse.register("std::map<{}, {}>")
@parse.register("std::unordered_map<{}, {}>")
@parse.register("std::multimap<{}, {}>")
@parse.register("std::unordered_multimap<{}, {}>")
def _(typename, keytype, valuetype, obj) -> str:
    assert isinstance(obj, list)
    rep = ", ".join(f"{{{parse(keytype, k)}, {parse(valuetype, v)}}}" for k, v in obj)
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