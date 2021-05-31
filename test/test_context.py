from datamatic import context, builtin
import pytest

@pytest.fixture()
def ctx():
    """
    Returns a context with the builtin dmx loaded.
    """
    ctx = context.Context({})
    builtin.main(ctx)
    return ctx


def test_parse_int(ctx):
    assert ctx.parse("int", 5) == "5"


def test_parse_float(ctx):
    assert ctx.parse("float", 5) == "5.0f"
    assert ctx.parse("float", 2.0) == "2.0f"


def test_parse_double(ctx):
    assert ctx.parse("double", 5) == "5.0"
    assert ctx.parse("double", 2.0) == "2.0"


def test_parse_bool(ctx):
    assert ctx.parse("bool", True) == "true"
    assert ctx.parse("bool", False) == "false"

    with pytest.raises(Exception):
        ctx.parse("bool", 1)  # No implicit conversion


def test_parse_string(ctx):
    assert ctx.parse("std::string", "Hello") == '"Hello"'


@pytest.mark.parametrize("container", [
    "std::vector",
    "std::deque",
    "std::queue",
    "std::stack",
    "std::list",
    "std::forward_list",
    "std::set",
    "std::unordered_set",
    "std::multiset",
    "std::unordered_multiset",
])
def test_parse_sequence(ctx, container):
    assert ctx.parse(f"{container}<int>", [1, 2, 3, 4]) == f"{container}<int>{{1, 2, 3, 4}}"

    with pytest.raises(Exception):
        ctx.parse(f"{container}<int>", 1)  # Object must be a list

    with pytest.raises(Exception):
        ctx.parse(f"{container}<int>", ["a", "b"])  # Object must be a list of ints


def test_parse_array(ctx):
    assert ctx.parse("std::array<int, 5>", [1, 2, 3, 4, 5]) == "std::array<int, 5>{1, 2, 3, 4, 5}"

    with pytest.raises(Exception):
        ctx.parse("std::array<int, 4>", [1, 2, 3, 4, 5])  # Not enough elements

    with pytest.raises(Exception):
        ctx.parse("std::array<int, 6>", [1, 2, 3, 4, 5])  # Too many elements


def test_parse_pair(ctx):
    assert ctx.parse("std::pair<int, float>", [2, 3.0]) == "std::pair<int, float>{2, 3.0f}"

    with pytest.raises(Exception):
        ctx.parse("std::pair<int, float>", 2)  # Must be a list

    with pytest.raises(Exception):
        ctx.parse("std::pair<int, float>", [2, 3.0, 1])  # Must be a list of two elements

    with pytest.raises(Exception):
        ctx.parse("std::pair<int, float>", [2, "a"])  # Element types must match


@pytest.mark.parametrize("container", [
    "std::map",
    "std::unordered_map",
    "std::multimap",
    "std::unordered_multimap",
])
def test_parse_mapping(ctx, container):
    expected = f"{container}<int, int>{{{{1, 2}}, {{3, 4}}}}"

    # List of pairs JSON object
    assert ctx.parse(f"{container}<int, int>", [[1, 2], [3, 4]]) == expected

    # Dict JSON object
    assert ctx.parse(f"{container}<int, int>", {1: 2, 3: 4}) == expected

    with pytest.raises(Exception):
        ctx.parse(f"{container}<int, int>", 1)  # Object must be a list or dict


def test_parse_optional(ctx):
    assert ctx.parse("std::optional<int>", 5) == "std::optional<int>{5}"
    assert ctx.parse("std::optional<int>", None) == "std::nullopt"


@pytest.mark.parametrize("ptr_type", ["unique", "shared"])
def test_parse_smart_pointer(ctx, ptr_type):
    assert ctx.parse(f"std::{ptr_type}_ptr<int>", 5) == f"std::make_{ptr_type}<int>(5)"
    assert ctx.parse(f"std::{ptr_type}_ptr<int>", None) == "nullptr"


def test_parse_weak_pointer(ctx):
    assert ctx.parse("std::weak_ptr<int>", None) == "nullptr"
    
    with pytest.raises(Exception):
        ctx.parse("std::weak_ptr<int>", 4)  # weak pointers can only be initialised to nullptr


@pytest.mark.parametrize("typ", ["std::any", "std::monostate"])
def test_parse_any_and_monostate(ctx, typ):
    assert ctx.parse(typ, None) == f"{typ}{{}}"

    with pytest.raises(Exception):
        ctx.parse(typ, 5)  # Can only default initialise


def test_parse_tuple(ctx):
    tuple_type = "std::tuple<int, float, double>"
    assert ctx.parse(tuple_type, [1, 1, 1]) == f"{tuple_type}{{1, 1.0f, 1.0}}"

    with pytest.raises(Exception):
        ctx.parse(tuple_type, [1, 2])  # Not enough elements

    with pytest.raises(Exception):
        ctx.parse(tuple_type, ["a", "b", "c"])  # Type mismatch


def test_parse_variant(ctx):
    # Value is parsed as the first successful type
    assert ctx.parse("std::variant<int, float>", 5) == "5"
    assert ctx.parse("std::variant<float, int>", 5) == "5.0f"
    assert ctx.parse("std::variant<int, std::string>", "Hello") == '"Hello"'
    assert ctx.parse("std::variant<int, std::map<int, int>>", {1: 2}) == "std::map<int, int>{{1, 2}}"

    with pytest.raises(Exception):
        ctx.parse("std::variant<int, std::string>", None)  # Value does not parse as any subtype


def test_parse_function(ctx):
    # No checks occur on std::function
    assert ctx.parse("std::function<int(bool)>", "a") == "a"


def test_typeparser_unregistered_type():
    # GIVEN
    ctx = context.Context({})

    # THEN
    with pytest.raises(Exception):
        ctx.parse("int", 4)  # Type is not registered


def test_typeparser_register():
    # GIVEN
    ctx = context.Context({})

    # WHEN
    @ctx.types.register("foo")
    def _(typename, obj):
        return f"{typename}, {obj}"

    # THEN
    assert ctx.parse("foo", None) == f"foo, None"


def test_typeparser_template_register():
    # GIVEN
    ctx = context.Context({})

    # WHEN
    @ctx.types.register("foo_{}")
    def _(typename, subtype, obj):
        return f"{typename}, {subtype}, {obj}"

    # THEN
    assert ctx.parse("foo_int", None) == f"foo_int, int, None"


def test_typeparser_variadic_register():
    # GIVEN
    ctx = context.Context({})

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


def test_custom_function_lookup_success():
    # GIVEN
    ctx = context.Context({})

    # WHEN
    @ctx.attrmethod("test.func")
    def func(attr):
        return "Foo"

    # THEN
    assert ctx.get("Attr", "test.func") == func


def test_custom_function_lookup_failure():
    # GIVEN
    ctx = context.Context({})

    # THEN
    with pytest.raises(Exception):
        ctx.get("Attr", "test.func")