"""
Test driver for the builtin comp and attr methods.
"""
from datamatic import method_register
import pytest
from unittest.mock import patch

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
    reg.attrmethod("test.func")(dummy)
    assert reg.get("Attr", "test.func") == dummy


def test_context_cannot_register_a_custom_method_twice(reg):
    reg.compmethod("foo")(dummy)
    with pytest.raises(RuntimeError):
        reg.compmethod("foo")(dummy)

    reg.attrmethod("bar")(dummy)
    with pytest.raises(RuntimeError):
        reg.attrmethod("bar")(dummy)


@pytest.mark.parametrize("namespace", [
    "Comp",
    "Attr"
])
@pytest.mark.parametrize("key,value", [
    ("name", "datamatic"),
    ("display_name", "Datamatic"),
    ("a", "abc"),
    (1, 2)
])
def test_property_access(reg, namespace, key, value):
    spec = {}  # Empty, as it wont be used here since we are just doing property lookup
    obj = {key: value}
    assert reg.get(namespace, key)(spec, obj) == value


def test_builtin_conditionals(reg, component):
    assert reg.get("Comp", "if_nth_else")([component], component, "0", "a", "b") == "a"
    assert reg.get("Comp", "if_nth_else")([component], component, "1", "a", "b") == "b"

    assert reg.get("Comp", "if_first")([component], component, "a") == "a"
    assert reg.get("Comp", "if_not_first")([component], component, "a") == ""
    assert reg.get("Comp", "if_last")([component], component, "a") == "a"
    assert reg.get("Comp", "if_not_last")([component], component, "a") == ""