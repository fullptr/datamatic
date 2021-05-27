"""
A module that holds CppType, a base class for classes that represent
C++ types. Users can subclass this to add their own types to
Datamatic.
"""
from functools import wraps


PARSERS = {}


def parse(typename, obj) -> str:
    """
    Parse the given object as the given type. A KeyError is raised if there is no
    parser registered for the given type.
    """
    return PARSERS[typename](typename, obj)


def register(typename):
    """
    A decorator to be used to register a function as the parser for the specified type.
    Functions that can be registered should have the signature (str, json_object).
    """
    def decorator(func):
        assert typename not in PARSERS
        PARSERS[typename] = func
        return func
    return decorator


@register("int")
def _(typename, obj) -> str:
    assert isinstance(obj, int)
    return str(obj)


@register("float")
def _(typename, obj) -> str:
    assert isinstance(obj, (int, float))
    if "." not in str(obj):
        return f"{obj}.0f"
    return f"{obj}f"


@register("double")
def _(typename, obj) -> str:
    assert isinstance(obj, (int, float))
    if "." not in str(obj):
        return f"{obj}.0"
    return f"{obj}"


@register("bool")
def _(typename, obj) -> str:
    assert isinstance(obj, bool)
    return "true" if obj else "false"


@register("std::string")
def _(typename, obj) -> str:
    assert isinstance(obj, str)
    return f'"{obj}"'