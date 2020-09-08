
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
    "Subtype",
    "Scriptable",
    "Savable",
    "Data",
    "Limits"
}

# Types -> Subtypes
ATTR_TYPES = {
    "bool",
    "int",
    "float",
    "std::string",
    "Maths::vec2",
    "Maths::vec3",
    "Maths::vec4",
    "Maths::quat",
    "Maths::mat4",
    "std::queue<Maths::vec3>" # TODO: Generalise this
}

ATTR_SUBTYPES = {
    "std::string": ["File"],
    "Maths::vec3": ["Colour"]
}

def check_bool(value):
    assert isinstance(value, bool), value

def check_int(value):
    assert isinstance(value, int), value

def check_float(value):
    assert isinstance(value, float), value

def check_std_string(value):
    assert isinstance(value, str), value

def check_vec(value, length):
    assert isinstance(value, list), value
    assert len(value) == length, value
    assert all(isinstance(x, float) for x in value), value

def check_mat4(value):
    assert value is None, "Matrices should be non-scriptable and have default null (for now)"

def check_queue(value):
    assert isinstance(value, list), value
    for x in value:
        check_vec(x, 3)

ATTR_DEFAULT_CHECKS = {
    "bool": check_bool,
    "int": check_int,
    "float": check_float,
    "std::string": check_std_string,
    "Maths::vec2": lambda val: check_vec(val, 2),
    "Maths::vec3": lambda val: check_vec(val, 3),
    "Maths::vec4": lambda val: check_vec(val, 4),
    "Maths::quat": lambda val: check_vec(val, 4),
    "Maths::mat4": check_mat4,
    "std::queue<Maths::vec3>": check_queue # TODO: Generalise this
}


def validate_attribute(attr):
    assert ATTR_KEYS_REQ <= set(attr.keys()), attr
    assert set(attr.keys()) <= ATTR_KEYS_REQ | ATTR_KEYS_OPT, attr

    assert isinstance(attr["Name"], str), attr
    assert isinstance(attr["DisplayName"], str), attr
    assert attr["Type"] in ATTR_TYPES, attr
    ATTR_DEFAULT_CHECKS[attr["Type"]](attr["Default"]), attr

    if attr["Type"] == "Maths::mat4": # TODO: Remove this
        assert attr["Scriptable"] is False, "Maths::mat4 is currently not scriptable"

    if "Subtype" in attr:
        assert attr["Subtype"] in ATTR_SUBTYPES[attr["Type"]], attr
    if "Scriptable" in attr:
        assert isinstance(attr["Scriptable"], bool), attr
    if "Savable" in attr:
        assert isinstance(attr["Savable"], bool), attr
    if "Data" in attr:
        assert isinstance(attr["Data"], str), attr
    if "Limits" in attr:
        limits = attr["Limits"]
        assert type(attr["Type"] in ["int", "float"]), attr
        assert isinstance(limits, list), attr
        assert len(limits) == 2, attr
        if attr["Type"] == "int":
            assert all([isinstance(x, int) for x in limits])
        else:
            assert all([isinstance(x, float) for x in limits])


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
    # First, check that the validator is in a correct state
    assert ATTR_TYPES == set(ATTR_DEFAULT_CHECKS.keys())
    assert set(ATTR_SUBTYPES.keys()) <= ATTR_TYPES

    # Now, validate the schema
    assert set(spec.keys()) == {"Version", "Components"}

    assert isinstance(spec["Version"], int)
    assert isinstance(spec["Components"], list)

    for comp in spec["Components"]:
        validate_component(comp)

    print("Schema Valid!")