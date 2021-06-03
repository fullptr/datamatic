from datamatic import context
import pytest


@pytest.fixture
def ctx():
    return context.Context({})


def dummy(typename, obj):
    return ""


def test_typeparser_unregistered_type(ctx):
    with pytest.raises(Exception):
        ctx.parse("int", 4)  # Type is not registered


def test_typeparser_register(ctx):
    # WHEN
    @ctx.types.register("foo")
    def _(typename, obj):
        return f"{typename}, {obj}"

    # THEN
    assert ctx.parse("foo", None) == f"foo, None"


def test_typeparser_template_register(ctx):
    # WHEN
    @ctx.types.register("foo_{}")
    def _(typename, subtype, obj):
        return f"{typename}, {subtype}, {obj}"

    # THEN
    assert ctx.parse("foo_int", None) == f"foo_int, int, None"


def test_typeparser_variadic_register(ctx):
    # WHEN
    @ctx.types.register("foo<{}...>")
    def _(typename, subtypes, obj):
        return f"{typename}, {subtypes}, {obj}"

    # THEN
    expected = f"foo<int, float, int>, ['int', 'float', 'int'], None"
    assert ctx.parse("foo<int, float, int>", None) == expected


def test_variadic_typelist_parser():
    assert context.parse_variadic_typelist("") == []
    assert context.parse_variadic_typelist("int") == ["int"]
    assert context.parse_variadic_typelist("int, float, std::map<int, int>") == ["int", "float", "std::map<int, int>"]
    assert context.parse_variadic_typelist("std::pair<a, b>, std::tuple<a, b, c>") == ["std::pair<a, b>", "std::tuple<a, b, c>"]

    assert context.parse_variadic_typelist("std::function<int(bool, float)>, int") == ["std::function<int(bool, float)>", "int"]
    
    with pytest.raises(Exception):
        context.parse_variadic_typelist("std::function<int(bool>)")  # Invalid bracket ordering
    
    with pytest.raises(Exception):
        context.parse_variadic_typelist("std::pair<")  # Invalid brackets


def test_custom_function_lookup_success(ctx):
    ctx.attrmethod("test.func")(dummy)
    assert ctx.get("Attr", "test.func") == dummy


def test_custom_function_lookup_failure(ctx):
    with pytest.raises(Exception):
        ctx.get("Attr", "test.func")


def test_typeparser_cannot_have_two_variadic_templates(ctx):
    with pytest.raises(RuntimeError):
        ctx.type("{}...{}...")(dummy)


@pytest.mark.parametrize("pattern", [
    "int", # standard
    "std::optional<{}>", # template
    "std::tuple<{}...>" # variadic
])
def test_typeparser_cannot_register_a_function_twice(ctx, pattern):
    ctx.type(pattern)(dummy)
    with pytest.raises(RuntimeError):
        ctx.type(pattern)(dummy)