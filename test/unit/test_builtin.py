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
        "default": 5,
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


def test_parse_int(ctx):
    assert ctx.parse("int", 5) == "5"


def test_parse_float(ctx):
    assert ctx.parse("float", 5) == "5.0f"
    assert ctx.parse("float", 2.0) == "2.0f"


def test_parse_double(ctx):
    assert ctx.parse("double", 5) == "5.0"
    assert ctx.parse("double", 2.0) == "2.0"

    with pytest.raises(RuntimeError):
        ctx.parse("double", [])  # Must be an int or float


def test_parse_bool(ctx):
    assert ctx.parse("bool", True) == "true"
    assert ctx.parse("bool", False) == "false"

    with pytest.raises(RuntimeError):
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

    with pytest.raises(RuntimeError):
        ctx.parse(f"{container}<int>", 1)  # Object must be a list

    with pytest.raises(RuntimeError):
        ctx.parse(f"{container}<int>", ["a", "b"])  # Object must be a list of ints


def test_parse_array(ctx):
    assert ctx.parse("std::array<int, 5>", [1, 2, 3, 4, 5]) == "std::array<int, 5>{1, 2, 3, 4, 5}"

    with pytest.raises(RuntimeError):
        ctx.parse("std::array<int, 4>", [1, 2, 3, 4, 5])  # Not enough elements

    with pytest.raises(RuntimeError):
        ctx.parse("std::array<int, 6>", [1, 2, 3, 4, 5])  # Too many elements

    with pytest.raises(RuntimeError):
        ctx.parse("std::array<int, a>", [1, 2])  # Second arg must be integral

    with pytest.raises(RuntimeError):
        ctx.parse("std::array<int, 5>", 5)  # Obj must be a list


def test_parse_pair(ctx):
    assert ctx.parse("std::pair<int, float>", [2, 3.0]) == "std::pair<int, float>{2, 3.0f}"

    with pytest.raises(RuntimeError):
        ctx.parse("std::pair<int, float>", 2)  # Must be a list

    with pytest.raises(RuntimeError):
        ctx.parse("std::pair<int, float>", [2, 3.0, 1])  # Must be a list of two elements

    with pytest.raises(RuntimeError):
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

    with pytest.raises(RuntimeError):
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
    
    with pytest.raises(RuntimeError):
        ctx.parse("std::weak_ptr<int>", 4)  # weak pointers can only be initialised to nullptr


@pytest.mark.parametrize("typ", ["std::any", "std::monostate"])
def test_parse_any_and_monostate(ctx, typ):
    assert ctx.parse(typ, None) == f"{typ}{{}}"

    with pytest.raises(RuntimeError):
        ctx.parse(typ, 5)  # Can only default initialise


def test_parse_tuple(ctx):
    tuple_type = "std::tuple<int, float, double>"
    assert ctx.parse(tuple_type, [1, 1, 1]) == f"{tuple_type}{{1, 1.0f, 1.0}}"

    with pytest.raises(RuntimeError):
        ctx.parse(tuple_type, [1, 2])  # Not enough elements

    with pytest.raises(RuntimeError):
        ctx.parse(tuple_type, ["a", "b", "c"])  # Type mismatch

    with pytest.raises(RuntimeError):
        ctx.parse(tuple_type, 5)  # Obj must be a list


def test_parse_variant(ctx):
    # Value is parsed as the first successful type
    assert ctx.parse("std::variant<int, float>", 5) == "5"
    assert ctx.parse("std::variant<float, int>", 5) == "5.0f"
    assert ctx.parse("std::variant<int, std::string>", "Hello") == '"Hello"'
    assert ctx.parse("std::variant<int, std::map<int, int>>", {1: 2}) == "std::map<int, int>{{1, 2}}"

    with pytest.raises(RuntimeError):
        ctx.parse("std::variant<int, std::string>", None)  # Value does not parse as any subtype


def test_parse_function(ctx):
    # No checks occur on std::function
    assert ctx.parse("std::function<int(bool)>", "a") == "a"

    with pytest.raises(RuntimeError):
        ctx.parse("std::function<int(bool)>", 5)  # Must be a string