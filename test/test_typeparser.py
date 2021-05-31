from datamatic import api, builtin
import pytest

@pytest.fixture()
def context():
    """
    Returns a context with the builtin dmx loaded.
    """
    context = api.Context()
    builtin.main(context)
    return context


def test_parse_int(context):
    assert context.types.parse("int", 5) == "5"


def test_parse_float(context):
    assert context.types.parse("float", 5) == "5.0f"
    assert context.types.parse("float", 2.0) == "2.0f"


def test_parse_double(context):
    assert context.types.parse("double", 5) == "5.0"
    assert context.types.parse("double", 2.0) == "2.0"


def test_parse_bool(context):
    assert context.types.parse("bool", True) == "true"
    assert context.types.parse("bool", False) == "false"

    with pytest.raises(Exception):
        context.types.parse("bool", 1)  # No implicit conversion


def test_parse_string(context):
    assert context.types.parse("std::string", "Hello") == '"Hello"'


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
def test_parse_sequence(context, container):
    assert context.types.parse(f"{container}<int>", [1, 2, 3, 4]) == f"{container}<int>{{1, 2, 3, 4}}"

    with pytest.raises(Exception):
        context.types.parse(f"{container}<int>", 1)  # Object must be a list

    with pytest.raises(Exception):
        context.types.parse(f"{container}<int>", ["a", "b"])  # Object must be a list of ints


def test_parse_array(context):
    assert context.types.parse("std::array<int, 5>", [1, 2, 3, 4, 5]) == "std::array<int, 5>{1, 2, 3, 4, 5}"

    with pytest.raises(Exception):
        context.types.parse("std::array<int, 4>", [1, 2, 3, 4, 5])  # Not enough elements

    with pytest.raises(Exception):
        context.types.parse("std::array<int, 6>", [1, 2, 3, 4, 5])  # Too many elements


def test_parse_pair(context):
    assert context.types.parse("std::pair<int, float>", [2, 3.0]) == "std::pair<int, float>{2, 3.0f}"

    with pytest.raises(Exception):
        context.types.parse("std::pair<int, float>", 2)  # Must be a list

    with pytest.raises(Exception):
        context.types.parse("std::pair<int, float>", [2, 3.0, 1])  # Must be a list of two elements

    with pytest.raises(Exception):
        context.types.parse("std::pair<int, float>", [2, "a"])  # Element types must match


@pytest.mark.parametrize("container", [
    "std::map",
    "std::unordered_map",
    "std::multimap",
    "std::unordered_multimap",
])
def test_parse_mapping(context, container):
    expected = f"{container}<int, int>{{{{1, 2}}, {{3, 4}}}}"

    # List of pairs JSON object
    assert context.types.parse(f"{container}<int, int>", [[1, 2], [3, 4]]) == expected

    # Dict JSON object
    assert context.types.parse(f"{container}<int, int>", {1: 2, 3: 4}) == expected

    with pytest.raises(Exception):
        context.types.parse(f"{container}<int, int>", 1)  # Object must be a list or dict


def test_parse_optional(context):
    assert context.types.parse("std::optional<int>", 5) == "std::optional<int>{5}"
    assert context.types.parse("std::optional<int>", None) == "std::nullopt"


@pytest.mark.parametrize("ptr_type", ["unique", "shared"])
def test_parse_smart_pointer(context, ptr_type):
    assert context.types.parse(f"std::{ptr_type}_ptr<int>", 5) == f"std::make_{ptr_type}<int>(5)"
    assert context.types.parse(f"std::{ptr_type}_ptr<int>", None) == "nullptr"


def test_parse_weak_pointer(context):
    assert context.types.parse("std::weak_ptr<int>", None) == "nullptr"
    
    with pytest.raises(Exception):
        context.types.parse("std::weak_ptr<int>", 4)  # weak pointers can only be initialised to nullptr


@pytest.mark.parametrize("typ", ["std::any", "std::monostate"])
def test_parse_any_and_monostate(context, typ):
    assert context.types.parse(typ, None) == f"{typ}{{}}"

    with pytest.raises(Exception):
        context.types.parse(typ, 5)  # Can only default initialise


def test_parse_tuple(context):
    tuple_type = "std::tuple<int, float, double>"
    assert context.types.parse(tuple_type, [1, 1, 1]) == f"{tuple_type}{{1, 1.0f, 1.0}}"

    with pytest.raises(Exception):
        context.types.parse(tuple_type, [1, 2])  # Not enough elements

    with pytest.raises(Exception):
        context.types.parse(tuple_type, ["a", "b", "c"])  # Type mismatch


def test_parse_variant(context):
    # Value is parsed as the first successful type
    assert context.types.parse("std::variant<int, float>", 5) == "5"
    assert context.types.parse("std::variant<float, int>", 5) == "5.0f"
    assert context.types.parse("std::variant<int, std::string>", "Hello") == '"Hello"'
    assert context.types.parse("std::variant<int, std::map<int, int>>", {1: 2}) == "std::map<int, int>{{1, 2}}"

    with pytest.raises(Exception):
        context.types.parse("std::variant<int, std::string>", None)  # Value does not parse as any subtype


def test_parse_function(context):
    # No checks occur on std::function
    assert context.types.parse("std::function<int(bool)>", "a") == "a"


def test_typeparser_unregistered_type():
    # GIVEN
    context = api.Context()

    # THEN
    with pytest.raises(Exception):
        context.types.parse("int", 4)  # Type is not registered


def test_typeparser_register():
    # GIVEN
    context = api.Context()

    # WHEN
    @context.types.register("foo")
    def _(typename, obj):
        return f"{typename}, {obj}"

    # THEN
    assert context.types.parse("foo", None) == f"foo, None"


def test_typeparser_template_register():
    # GIVEN
    context = api.Context()

    # WHEN
    @context.types.register("foo_{}")
    def _(typename, subtype, obj):
        return f"{typename}, {subtype}, {obj}"

    # THEN
    assert context.types.parse("foo_int", None) == f"foo_int, int, None"


def test_typeparser_variadic_register():
    # GIVEN
    context = api.Context()

    # WHEN
    @context.types.register("foo<{}...>")
    def _(typename, subtypes, obj):
        return f"{typename}, {subtypes}, {obj}"

    # THEN
    expected = f"foo<int, float, int>, ['int', 'float', 'int'], None"
    assert context.types.parse("foo<int, float, int>", None) == expected


def test_variadic_typelist_parser():
    assert api.parse_variadic_typelist("") == []
    assert api.parse_variadic_typelist("int") == ["int"]
    assert api.parse_variadic_typelist("int, float, std::map<int, int>") == ["int", "float", "std::map<int, int>"]
    assert api.parse_variadic_typelist("std::pair<a, b>, std::tuple<a, b, c>") == ["std::pair<a, b>", "std::tuple<a, b, c>"]

    assert api.parse_variadic_typelist("std::function<int(bool, float)>, int") == ["std::function<int(bool, float)>", "int"]
    
    with pytest.raises(Exception):
        api.parse_variadic_typelist("std::function<int(bool>)")  # Invalid bracket ordering
    
    with pytest.raises(Exception):
        api.parse_variadic_typelist("std::pair<")  # Invalid brackets