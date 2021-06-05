"""
Test driver for the builtin comp and attr methods.
"""
from datamatic import context, builtin
import pytest

@pytest.fixture
def reg():
    """
    Returns a method register with the builtin dmx loaded.
    """
    method_register = context.MethodRegister()
    builtin.main(method_register)
    return method_register


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
    spec = {
        "components": [component]
    }

    assert reg.get("Comp", "if_nth_else")(spec, component, "0", "a", "b") == "a"
    assert reg.get("Comp", "if_nth_else")(spec, component, "1", "a", "b") == "b"

    assert reg.get("Comp", "if_first")(spec, component, "a") == "a"
    assert reg.get("Comp", "if_not_first")(spec, component, "a") == ""
    assert reg.get("Comp", "if_last")(spec, component, "a") == "a"
    assert reg.get("Comp", "if_not_last")(spec, component, "a") == ""