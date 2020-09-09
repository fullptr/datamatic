from Datamatic import Types

COMP_KEYS_REQ = {
    "Name",
    "DisplayName",
    "Attributes"
}

COMP_KEYS_OPT = {
    "Scriptable"
}

ATTR_KEYS_REQ = {
    "Name",
    "DisplayName",
    "Type",
    "Default"
}

ATTR_KEYS_OPT = {
    "Scriptable",
    "Savable",
    "Data",
}

def validate_attribute(attr):
    assert ATTR_KEYS_REQ <= set(attr.keys()), attr
    assert set(attr.keys()) <= ATTR_KEYS_REQ | ATTR_KEYS_OPT, attr

    assert isinstance(attr["Name"], str), attr
    assert isinstance(attr["DisplayName"], str), attr

    cls = Types.get(attr["Type"])
    assert cls is not None
    obj = cls(attr["Default"]) # Will assert if invalid

    if attr["Type"] == "Maths::mat4": # TODO: Remove this
        assert attr["Scriptable"] is False, "Maths::mat4 is currently not scriptable"

    if "Scriptable" in attr:
        assert isinstance(attr["Scriptable"], bool), attr
    if "Savable" in attr:
        assert isinstance(attr["Savable"], bool), attr


def validate_component(comp):
    assert COMP_KEYS_REQ <= set(comp.keys()), comp
    assert set(comp.keys()) <= COMP_KEYS_REQ | COMP_KEYS_OPT, comp

    assert isinstance(comp["Name"], str), comp
    assert isinstance(comp["DisplayName"], str), comp
    assert isinstance(comp["Attributes"], list), comp

    if "Scriptable" in comp:
        assert isinstance(comp["Scriptable"], bool)

    for attr in comp["Attributes"]:
        validate_attribute(attr)


def validate(spec):
    # Now, validate the schema
    assert set(spec.keys()) == {"Version", "Components"}

    assert isinstance(spec["Version"], int)
    assert isinstance(spec["Components"], list)

    for comp in spec["Components"]:
        validate_component(comp)

    print("Schema Valid!")