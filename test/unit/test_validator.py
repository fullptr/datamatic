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


def test_validate_attribute_missing_required_key():
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute({}, [])


def test_validate_attribute_unknown_keys():
    attr = {
        "name": "",
        "display_name": "",
        "type": "int",
        "default": "4",
        "extra": None
    }

    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [])


def test_validate_attribute_types():
    attr = { "name": None, "display_name": "Display", "type": "int", "default": "0" }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [])

    attr = { "name": "Name", "display_name": None, "type": "int", "default": "0" }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [])

    attr = { "name": "Name", "display_name": "Display", "type": None, "default": "0" }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [])

    attr = { "name": "Name", "display_name": "Display", "type": "int", "default": None }
    with pytest.raises(InvalidSpecError):
        validator.validate_attribute(attr, [])


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

    # "name" must be a str
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({"name": True, "default": False})

    # "default" must be a bool
    with pytest.raises(InvalidSpecError):
        validator.validate_flags_in_spec({"name": "flag", "default": "False"})


def test_validate_component_missing_required_key():
    comp = {}

    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [])


def test_validate_component_unknown_keys():
    comp = {
        "name": "",
        "display_name": "",
        "attributes": [],
        "extra": None
    }

    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [])


def test_validate_component_types():
    comp = { "name": None, "display_name": "Display", "attributes": [] }
    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [])

    comp = { "name": "Name", "display_name": None, "attributes": [] }
    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [])

    comp = { "name": "Name", "display_name": "Display", "attributes": None }
    with pytest.raises(InvalidSpecError):
        validator.validate_component(comp, [])


def test_validator_run():
    # doesn't have the correct keys
    spec = {}
    with pytest.raises(InvalidSpecError):
        validator.run(spec)

    # has invalid extra keys
    spec = {"flags": [], "components": [], "extra": []}
    with pytest.raises(InvalidSpecError):
        validator.run(spec)


def test_validator_flags_must_be_a_list():
    spec = {"flags": None, "components": []}
    with pytest.raises(InvalidSpecError):
        validator.run(spec)


def test_validator_components_must_be_a_list():
    spec = {"flags": [], "components": None}
    with pytest.raises(InvalidSpecError):
        validator.run(spec)