from datamatic import context
import pytest


@pytest.fixture
def ctx():
    return context.Context({})


def dummy(typename, obj):
    return ""


def test_custom_function_lookup_success(ctx):
    ctx.attrmethod("test.func")(dummy)
    assert ctx.get("Attr", "test.func") == dummy


def test_custom_function_lookup_failure(ctx):
    with pytest.raises(RuntimeError):
        ctx.get("Attr", "test.func")


def test_context_cannot_register_a_custom_method_twice(ctx):
    ctx.compmethod("foo")(dummy)
    with pytest.raises(RuntimeError):
        ctx.compmethod("foo")(dummy)

    ctx.attrmethod("bar")(dummy)
    with pytest.raises(RuntimeError):
        ctx.attrmethod("bar")(dummy)