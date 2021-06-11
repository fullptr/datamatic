"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""


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


def validate_flags_on_object(flags, flag_names):
    """
    Given an object, verify that it is a (str -> bool) dict.
    """
    assert_type(flags, dict)
    if set(flags.keys()) != flag_names:
        raise InvalidSpecError(f"Invalid flags set, got {set(flags.keys())}, expected {flag_names}")

    for key, value in flags.items():
        assert_type(key, str)
        assert_type(value, bool)


def validate_attribute(attr, flag_names):
    assert_property(attr, "flags")
    validate_flags_on_object(attr["flags"], flag_names)


def validate_component(comp, flag_names):
    """
    Asserts that the given component is well-formed.
    """
    assert_property(comp, "flags")
    validate_flags_on_object(comp["flags"], flag_names)

    assert_property(comp, "attributes")
    assert_type(comp["attributes"], list)
    for attr in comp["attributes"]:
        validate_attribute(attr, flag_names)


def run(spec):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    if "flag_defaults" not in spec:
        raise InvalidSpecError("Spec must contain 'flag_defaults'")
    if "components" not in spec:
        raise InvalidSpecError("Spec must contain 'components'")

    spec_flags = spec["flag_defaults"]
    assert_type(spec_flags, dict)
    for flag_name, value in spec_flags.items():
        assert_type(flag_name, str)
        assert_type(value, bool)

    spec_components = spec["components"]
    assert_type(spec_components, list)

    flag_names = set(spec_flags.keys())

    for comp in spec["components"]:
        validate_component(comp, flag_names)

    print("Schema Valid!")
