"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""
import plugins


COMP_KEYS_REQ = {
    "name",
    "display_name",
    "attributes"
}


COMP_KEYS_OPT = {
    "flags"
}


ATTR_KEYS_REQ = {
    "name",
    "display_name",
    "type",
    "default"
}


ATTR_KEYS_OPT = {
    "flags",
    "custom"
}


FLAG_KEYS = {
    "name",
    "default"
}


def validate_attribute(attr, flags):
    """
    Asserts that the given attribute is well-formed.
    """
    assert ATTR_KEYS_REQ <= set(attr.keys()), attr
    assert set(attr.keys()) <= ATTR_KEYS_REQ | ATTR_KEYS_OPT, attr

    assert isinstance(attr["name"], str), attr
    assert isinstance(attr["display_name"], str), attr

    # Verify that accessing the default value succeeds.
    plugins.builtin.default(attr)

    if "flags" in attr:
        assert isinstance(attr["flags"], dict)
        for key, val in attr["flags"].items():
            assert key in flags, f"{key} is not a valid flag"
            assert isinstance(key, str), attr
            assert isinstance(val, bool), attr


def validate_flag(flag):
    """
    Asserts that the given flag is well-formed.
    """
    assert set(flag.keys()) == FLAG_KEYS, flag
    assert isinstance(flag["name"], str), flag
    assert isinstance(flag["default"], bool), flag


def validate_component(comp, flags):
    """
    Asserts that the given component is well-formed.
    """
    assert COMP_KEYS_REQ <= set(comp.keys()), comp
    assert set(comp.keys()) <= COMP_KEYS_REQ | COMP_KEYS_OPT, comp

    assert isinstance(comp["name"], str), comp
    assert isinstance(comp["display_name"], str), comp
    assert isinstance(comp["attributes"], list), comp

    if "flags" in comp:
        assert isinstance(comp["flags"], dict)
        for key, val in comp["flags"].items():
            assert key in flags, f"{key} is not a valid flag"
            assert isinstance(key, str), comp
            assert isinstance(val, bool), comp

    for attr in comp["attributes"]:
        validate_attribute(attr, flags)


def run(spec):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    assert set(spec.keys()) == {"flags", "components"}

    assert isinstance(spec["flags"], list)
    assert isinstance(spec["components"], list)

    for flag in spec["flags"]:
        validate_flag(flag)

    flags = {flag["name"] for flag in spec["flags"]}

    for comp in spec["components"]:
        validate_component(comp, flags)

    print("Schema Valid!")
