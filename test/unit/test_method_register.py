"""
Test driver for the builtin comp and attr methods.
"""
from datamatic import method_register, generator
import pytest


@pytest.fixture
def reg():
    """
    Returns a method register with the builtin dmx loaded.
    """
    mreg = method_register.MethodRegister()
    mreg.load_builtins()
    return mreg


@pytest.fixture
def component():
    """
    Returns a test component.
    """
    return {
        "name": "foo",
        "display_name": "Foo",
        "attributes": []
    }


@pytest.fixture
def attribute():
    """
    Returns a test attribute.
    """
    return {
        "name": "foo",
        "display_name": "Foo",
        "type": "int",
        "default": "5",
        "custom_key": None
    }


def dummy(spec, obj):
    return ""


def test_custom_function_lookup_success(reg):
    reg.attrmethod(dummy)
    assert reg.get("Attr", "dummy") == dummy


def test_context_cannot_register_a_custom_method_twice(reg):
    reg.compmethod(dummy)
    with pytest.raises(RuntimeError):
        reg.compmethod(dummy)

    reg.attrmethod(dummy)
    with pytest.raises(RuntimeError):
        reg.attrmethod(dummy)


@pytest.mark.parametrize("key,value", [
    ("name", "datamatic"),
    ("display_name", "Datamatic"),
    ("a", "abc"),
    (1, 2)
])
def test_property_access_comp(reg, key, value):
    comp = {key: value}
    ctx = generator.Context(spec=[comp], comp=comp, attr=None)
    assert reg.get("Comp", key)(ctx) == value


@pytest.mark.parametrize("key,value", [
    ("name", "datamatic"),
    ("display_name", "Datamatic"),
    ("a", "abc"),
    (1, 2)
])
def test_property_access_attr(reg, key, value):
    attr = {key: value}
    comp = {"attributes": [attr]}
    ctx = generator.Context(spec=[], comp=comp, attr=attr)
    assert reg.get("Attr", key)(ctx) == value


def test_builtin_conditionals_comp(reg, component):
    ctx = generator.Context(spec=[component], comp=component, attr=None)

    assert reg.get("Comp", "if_nth_else")(ctx, 0, "a", "b") == "a"
    assert reg.get("Comp", "if_nth_else")(ctx, 1, "a", "b") == "b"

    assert reg.get("Comp", "if_first")(ctx, "a") == "a"
    assert reg.get("Comp", "if_not_first")(ctx, "a") == ""
    assert reg.get("Comp", "if_last")(ctx, "a") == "a"
    assert reg.get("Comp", "if_not_last")(ctx, "a") == ""


def test_builtin_conditionals_attr(reg, attribute):
    comp = {"attributes": [attribute]}
    ctx = generator.Context(spec=[comp], comp=comp, attr=attribute)

    assert reg.get("Attr", "if_nth_else")(ctx, 0, "a", "b") == "a"
    assert reg.get("Attr", "if_nth_else")(ctx, 1, "a", "b") == "b"

    assert reg.get("Attr", "if_first")(ctx, "a") == "a"
    assert reg.get("Attr", "if_not_first")(ctx, "a") == ""
    assert reg.get("Attr", "if_last")(ctx, "a") == "a"
    assert reg.get("Attr", "if_not_last")(ctx, "a") == ""