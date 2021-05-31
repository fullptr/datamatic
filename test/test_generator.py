from datamatic import generator
from datamatic.generator import Token
import pytest


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