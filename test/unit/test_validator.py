"""
Validator unit tests.
"""
from datamatic import validator, context, builtin
from datamatic.validator import InvalidSpecError
import pytest


@pytest.fixture
def ctx():
    c = context.Context({})
    builtin.main(c)
    return c


def test_validate_attribute_missing_required_key(ctx):
    attr = {}

    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)


def test_validate_attribute_unknown_keys(ctx):
    attr = {
        "name": "",
        "display_name": "",
        "type": "int",
        "default": 0,
        "extra": None
    }

    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)


def test_validate_attribute_types(ctx):
    attr = { "name": None, "display_name": "Display", "type": "int", "default": 0 }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)

    attr = { "name": "Name", "display_name": None, "type": "int", "default": 0 }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)

    attr = { "name": "Name", "display_name": "Display", "type": None, "default": 0 }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)


def test_validate_flags_on_object():
    # obj must be a dict
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_on_object([], set())

    # foo is not a valid flag
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_on_object({"foo": True}, {"bar"})

    # keys must be a str
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_on_object({1: True}, {1})

    # value must be a bool
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_on_object({"foo": 1}, {"foo"})


def test_validate_flags_in_spec():
    # flag must have "name" and "default" as keys
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({})

    # flag must only have those keys
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({"name": "foo", "default": True, "a": None})

    # key must be a string
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({1: True})

    # value must be a bool
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({"name": 1})


def test_validate_component_missing_required_key(ctx):
    comp = {}

    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [], ctx)


def test_validate_component_unknown_keys(ctx):
    comp = {
        "name": "",
        "display_name": "",
        "attributes": [],
        "extra": None
    }

    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [], ctx)


def test_validate_component_types(ctx):
    attr = { "name": None, "display_name": "Display", "attributes": [] }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)

    attr = { "name": "Name", "display_name": None, "attributes": [] }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)

    attr = { "name": "Name", "display_name": "Display", "attributes": None }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [], ctx)


def test_validator_run(ctx):
    # doesn't have the correct keys
    with pytest.raises(InvalidSpecError):
        validator.run(ctx)

    # has invalid extra keys
    ctx.spec = {"flags": [], "components": [], "extra": []}
    with pytest.raises(InvalidSpecError):
        validator.run(ctx)


def test_validator_flags_must_be_a_list(ctx):
    ctx.spec = {"flags": None, "components": []}
    with pytest.raises(InvalidSpecError):
        validator.run(ctx)


def test_validator_components_must_be_a_list(ctx):
    ctx.spec = {"flags": [], "components": None}
    with pytest.raises(InvalidSpecError):
        validator.run(ctx)