from datamatic import context
import pytest


@pytest.fixture
def reg():
    return context.MethodRegister()


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