"""
Test driver for the builtin comp and attr methods.
"""
from datamatic import context, builtin
import pytest

@pytest.fixture
def ctx():
    """
    Returns a context with the builtin dmx loaded.
    """
    ctx = context.Context({})
    builtin.main(ctx)
    return ctx


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
    }


def test_builtin_accessors(ctx, component, attribute):
    assert ctx.get("Comp", "name")(component) == "foo"
    assert ctx.get("Attr", "name")(attribute) == "foo"

    assert ctx.get("Comp", "display_name")(component) == "Foo"
    assert ctx.get("Attr", "display_name")(attribute) == "Foo"

    assert ctx.get("Attr", "type")(attribute) == "int"
    assert ctx.get("Attr", "default")(attribute) == "5"


def test_builtin_conditionals(ctx, component):
    # For these tests, there needs to be a spec in the context
    ctx.spec = {
        "flags": [],
        "components": [component]
    }

    assert ctx.get("Comp", "if_nth_else")(component, "0", "a", "b") == "a"
    assert ctx.get("Comp", "if_nth_else")(component, "1", "a", "b") == "b"

    assert ctx.get("Comp", "if_first")(component, "a") == "a"
    assert ctx.get("Comp", "if_not_first")(component, "a") == ""
    assert ctx.get("Comp", "if_last")(component, "a") == "a"
    assert ctx.get("Comp", "if_not_last")(component, "a") == ""