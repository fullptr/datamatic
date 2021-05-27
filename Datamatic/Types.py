"""
A module that holds CppType, a base class for classes that represent
C++ types. Users can subclass this to add their own types to
Datamatic.
"""
import functools


class SingleDispatch:
    """
    A decorator class designed to implement single dispatch on the first argument of a function.
    """
    def __init__(self, func):
        self.func = func
        self.dispatchers = {}

    def __call__(self, first, *args, **kwargs):
        if first not in self.dispatchers:
            return self.func(first, *args, **kwargs)
        return self.dispatchers[first](first, *args, **kwargs)

    def register(self, first, **kwargs):
        def decorator(func):
            assert first not in self.dispatchers, f"'{first}' already has a registered parser"
            new_func = functools.partial(func, **kwargs)
            self.dispatchers[first] = new_func
            return new_func
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