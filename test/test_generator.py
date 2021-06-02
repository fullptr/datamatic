from datamatic import generator
from datamatic.generator import Token
import pytest
from pathlib import Path


@pytest.mark.parametrize("raw,token", [
    ("Comp::foo", Token("Comp", "foo", tuple())),
    ("Comp::foo(a)", Token("Comp", "foo", ("a",))),
    ("Comp::foo(a|b)", Token("Comp", "foo", ("a", "b"))),
    ("Comp::foo(a|b|c)", Token("Comp", "foo", ("a", "b", "c"))),

    ("Comp::foo.bar", Token("Comp", "foo.bar", tuple())),
    ("Comp::foo.bar(a)", Token("Comp", "foo.bar", ("a",))),
    ("Comp::foo.bar(a|b)", Token("Comp", "foo.bar", ("a", "b"))),
    ("Comp::foo.bar(a|b|c)", Token("Comp", "foo.bar", ("a", "b", "c"))),

    ("Comp::foo.bar.baz", Token("Comp", "foo.bar.baz", tuple())),
    ("Comp::foo.bar.baz(a)", Token("Comp", "foo.bar.baz", ("a",))),
    ("Comp::foo.bar.baz(a|b)", Token("Comp", "foo.bar.baz", ("a", "b"))),
    ("Comp::foo.bar.baz(a|b|c)", Token("Comp", "foo.bar.baz", ("a", "b", "c"))),
])
def test_parse_token_string_success(raw, token):
    assert token == generator.parse_token_string(raw)


def test_empty_parentheses_is_valid():
    assert generator.parse_token_string("Comp::foo()") == Token("Comp", "foo", tuple())


@pytest.mark.parametrize("raw", [
    "Comp",
    "Comp::foo::bar"
    "Comp::foo(a"
    "Comp::foo(a|"
    "Comp::foo(a|b|)"
])
def test_parse_token_string_failure(raw):
    with pytest.raises(Exception):
        generator.parse_token_string(raw)


def test_flag_filtering():
    obj1 = {"flags": {"flag1": True, "flag2": False}}
    obj2 = {"flags": {"flag1": True, "flag2": True}}
    obj3 = {"flags": {"flag1": False, "flag2": False}}
    obj4 = {"flags": {"flag1": True, "flag2": True}}
    objects = [obj1, obj2, obj3, obj4]

    assert list(generator.flag_filter(objects, {"flag1": True, "flag2": True})) == [obj2, obj4]
    assert list(generator.flag_filter(objects, {"flag1": True, "flag2": False})) == [obj1]
    assert list(generator.flag_filter(objects, {"flag1": False, "flag2": True})) == []
    assert list(generator.flag_filter(objects, {"flag1": False, "flag2": False})) == [obj3]


def test_parse_flag_value():
    assert generator.parse_flag_val("true") == True
    assert generator.parse_flag_val("false") == False

    with pytest.raises(Exception):
        generator.parse_flag_val("a")


def test_get_header():
    assert generator.get_header(Path("file.h")) == "// GENERATED FILE\n"
    assert generator.get_header(Path("file.hpp")) == "// GENERATED FILE\n"
    assert generator.get_header(Path("file.cpp")) == "// GENERATED FILE\n"
    assert generator.get_header(Path("file.lua")) == "-- GENERATED FILE\n"

