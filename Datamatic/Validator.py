"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""
from Datamatic import Types


COMP_KEYS_REQ = {
    "Name",
    "DisplayName",
    "Attributes"
}


COMP_KEYS_OPT = {
    "Flags"
}


ATTR_KEYS_REQ = {
    "Name",
    "DisplayName",
    "Type",
    "Default"
}


ATTR_KEYS_OPT = {
    "Flags",
    "Custom"
}


FLAG_KEYS = {
    "Name",
    "Default"
}


def validate_attribute(attr):
    """
    Asserts that the given attribute is well-formed.
    """
    assert ATTR_KEYS_REQ <= set(attr.keys()), attr
    assert set(attr.keys()) <= ATTR_KEYS_REQ | ATTR_KEYS_OPT, attr

    assert isinstance(attr["Name"], str), attr
    assert isinstance(attr["DisplayName"], str), attr

    cls = Types.get(attr["Type"])
    assert cls is not None
    cls(attr["Default"]) # Will assert if invalid

    if "Flags" in attr:
        assert isinstance(attr["Flags"], dict)
        for key, val in attr["Flags"].items():
            assert isinstance(key, str)
            assert isinstance(val, bool)


def validate_flag(flag):
    """
    Asserts that the given flag is well-formed.
    """
    assert set(flag.keys()) == FLAG_KEYS
    assert isinstance(flag["Name"], str)
    assert isinstance(flag["Default"], bool)


def validate_component(comp):
    """
    Asserts that the given component is well-formed.
    """
    assert COMP_KEYS_REQ <= set(comp.keys()), comp
    assert set(comp.keys()) <= COMP_KEYS_REQ | COMP_KEYS_OPT, comp

    assert isinstance(comp["Name"], str), comp
    assert isinstance(comp["DisplayName"], str), comp
    assert isinstance(comp["Attributes"], list), comp

    if "Flags" in comp:
        assert isinstance(comp["Flags"], dict)
        for key, val in comp["Flags"].items():
            assert isinstance(key, str)
            assert isinstance(val, bool)

    for attr in comp["Attributes"]:
        validate_attribute(attr)


def run(spec):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    assert set(spec.keys()) == {"Version", "Flags", "Components"}

    assert isinstance(spec["Version"], int)
    assert isinstance(spec["Flags"], list)
    assert isinstance(spec["Components"], list)

    for flag in spec["Flags"]:
        validate_flag(flag)

    for comp in spec["Components"]:
        validate_component(comp)

    print("Schema Valid!")