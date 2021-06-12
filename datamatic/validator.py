"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""
from typing import Optional


class InvalidSpecError(RuntimeError):
    """
    Raised if the validation step on the spec file fails.
    """


def assert_type(object, expected_type):
    if not isinstance(object, expected_type):
        raise InvalidSpecError(f"{object=} must be a {expected_type}, got {type(object)}")


def assert_property(object, property: str):
    if property not in object:
        raise InvalidSpecError(f"'{property}' is missing from {object}")


def validate_flags_on_object(obj, flag_names: Optional[set[str]]):
    """
    Given an object, verify that it is a (str -> bool) dict.
    """
    flags = obj.get("flags")

    # If there are no default values for flags, then this spec is not making use of flags,
    # so components/attributes should not have a "flags" field.
    if flag_names is None and flags is not None:
        raise InvalidSpecError(f"'default_flags' is not provided, but flags exist on {obj}")

    assert_type(flags, dict)
    if set(flags.keys()) != flag_names:
        raise InvalidSpecError(f"Invalid flags set, got {set(flags.keys())}, expected {flag_names}")

    for key, value in flags.items():
        assert_type(key, str)
        assert_type(value, bool)


def validate_attribute(attr, flag_names: Optional[set[str]]):
    assert_property(attr, "flags")
    validate_flags_on_object(attr, flag_names)


def validate_component(comp, flag_names: Optional[set[str]]):
    """
    Asserts that the given component is well-formed.
    """
    assert_property(comp, "flags")
    validate_flags_on_object(comp, flag_names)

    assert_property(comp, "attributes")
    assert_type(comp["attributes"], list)
    for attr in comp["attributes"]:
        validate_attribute(attr, flag_names)


def run(spec):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    for key in spec:
        if key not in {"flag_defaults", "components"}:
            raise InvalidSpecError(f"Spec has invalid top-level key: {key}")
            
    flag_names: Optional[set[str]] = None
    if spec_flags := spec.get("flag_defaults"):
        assert_type(spec_flags, dict)
        flag_names = set(spec_flags.keys())
        for flag_name, value in spec_flags.items():
            assert_type(flag_name, str)
            assert_type(value, bool)

    if "components" not in spec:
        raise InvalidSpecError("Spec must contain 'components'")
    spec_components = spec["components"]
    assert_type(spec_components, list)

    for comp in spec["components"]:
        validate_component(comp, flag_names)

    print("Schema Valid!")
