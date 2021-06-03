"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""


class InvalidSpecError(RuntimeError):
    """
    Raised if the validation step on the spec file fails.
    """


SCHEMA_KEYS = {
    "flags",
    "components"
}


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


def validate_attribute(attr, flags, context):
    """
    Asserts that the given attribute is well-formed.
    """
    if set(attr.keys()) < ATTR_KEYS_REQ:
        raise InvalidSpecError(f"Missing keys for {attr}: {ATTR_KEYS_REQ - set(attr.keys())}")
    if ATTR_KEYS_REQ | ATTR_KEYS_OPT < set(attr.keys()):
        raise InvalidSpecError(f"Unrecognised keys for {attr}: {set(attr.keys()) - ATTR_KEYS_REQ | ATTR_KEYS_OPT}")

    if not isinstance(attr["name"], str):
        raise InvalidSpecError(f"{attr['name']=} must be a {str}, got {type(attr['name'])}")
    if not isinstance(attr["display_name"], str):
        raise InvalidSpecError(f"{attr['display_name']=} must be a {str}, got {type(attr['display_name'])}")

    # Verify that accessing the default value succeeds.
    context.get("Attr", "default")(attr)

    if "flags" in attr:
        if not isinstance(attr["flags"], dict):
            raise InvalidSpecError(f"{attr['flags']=} must be a {dict}, got {type(attr['display_name'])}")
        for key, val in attr["flags"].items():
            if key not in flags:
                raise InvalidSpecError(f"{key} is not a valid flag")
            if not isinstance(key, str):
                raise InvalidSpecError(f"{key=} must be a {str}, got {type(key)}")
            if not isinstance(val, bool):
                raise InvalidSpecError(f"{val=} must be a {bool}, got {type(key)}")


def validate_flag(flag):
    """
    Asserts that the given flag is well-formed.
    """
    if set(flag.keys()) != FLAG_KEYS:
        raise InvalidSpecError(f"Incorrect keys for flag declaration, got {set(flag.keys())}, needed {FLAG_KEYS}")
    if not isinstance(flag["name"], str):
        raise InvalidSpecError(f"{flag['name']=} must be a {str}, got {type(flag['name'])}")
    if not isinstance(flag["default"], bool):
        raise InvalidSpecError(f"{flag['default']=} must be a {bool}, got {type(flag['default'])}")


def validate_component(comp, flags, plugin_list):
    """
    Asserts that the given component is well-formed.
    """
    if set(comp.keys()) < COMP_KEYS_REQ:
        raise InvalidSpecError(f"Missing keys for {comp}: {COMP_KEYS_REQ - set(comp.keys())}")
    if COMP_KEYS_REQ | COMP_KEYS_OPT < set(comp.keys()):
        raise InvalidSpecError(f"Unrecognised keys for {comp}: {set(comp.keys()) - COMP_KEYS_REQ | COMP_KEYS_OPT}")

    if not isinstance(comp["name"], str):
        raise InvalidSpecError(f"{comp['name']=} must be a {str}, got {type(comp['name'])}")
    if not isinstance(comp["display_name"], str):
        raise InvalidSpecError(f"{comp['display_name']=} must be a {str}, got {type(comp['display_name'])}")
    if not isinstance(comp["attributes"], list):
        raise InvalidSpecError(f"{comp['attributes']=} must be a {list}, got {type(comp['attributes'])}")

    if "flags" in comp:
        if not isinstance(comp["flags"], dict):
            raise InvalidSpecError(f"{comp['flags']=} must be a {dict}, got {type(comp['display_name'])}")
        for key, val in comp["flags"].items():
            if key not in flags:
                raise InvalidSpecError(f"{key} is not a valid flag")
            if not isinstance(key, str):
                raise InvalidSpecError(f"{key=} must be a {str}, got {type(key)}")
            if not isinstance(val, bool):
                raise InvalidSpecError(f"{val=} must be a {bool}, got {type(key)}")

    for attr in comp["attributes"]:
        validate_attribute(attr, flags, plugin_list)


def run(context):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    if set(context.spec.keys()) != SCHEMA_KEYS:
        raise InvalidSpecError(f"Incorrect keys for flag declaration, got {set(context.spec.keys())}, needed {SCHEMA_KEYS}")

    spec_flags = context.spec["flags"]
    if not isinstance(spec_flags, list):
        raise InvalidSpecError(f"{spec_flags=} must be a {list}, got {type(spec_flags)}")

    spec_components = context.spec["flags"]
    if not isinstance(spec_flags, list):
        raise InvalidSpecError(f"{spec_components=} must be a {list}, got {type(spec_components)}")

    for flag in context.spec["flags"]:
        validate_flag(flag)

    flags = {flag["name"] for flag in context.spec["flags"]}

    for comp in context.spec["components"]:
        validate_component(comp, flags, context)

    print("Schema Valid!")
