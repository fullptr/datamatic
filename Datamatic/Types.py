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


@parse.register("std::map<{}, {}>")
@parse.register("std::unordered_map<{}, {}>")
@parse.register("std::multimap<{}>")
@parse.register("std::unordered_multimap<{}>")
def _(typename, keytype, valuetype, obj) -> str:
    assert isinstance(obj, list)
    rep = ", ".join(f"{{{parse(keytype, k)}, {parse(valuetype, v)}}}" for k, v in obj)
    return f"{typename}{{{rep}}}"