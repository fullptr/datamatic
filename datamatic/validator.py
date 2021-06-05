"""
Validates a given schema to make sure it is well-formed. This should
also serve as documentation for what makes a valid schema.
"""
from typing import Dict, Set


class InvalidSpecError(RuntimeError):
    """
    Raised if the validation step on the spec file fails.
    """


SCHEMA_KEYS = {
    "flag_defaults",
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


def validate_flags_on_object(obj, flags):
    """
    Given an object, verify that it is a (str -> bool) dict.
    """
    if not isinstance(obj, dict):
        raise InvalidSpecError(f"{obj=} must be a {dict}, got {type(obj)}")
    for key, val in obj.items():
        if key not in flags:
            raise InvalidSpecError(f"{key} is not a valid flag")
        if not isinstance(key, str):
            raise InvalidSpecError(f"{key=} must be a {str}, got {type(key)}")
        if not isinstance(val, bool):
            raise InvalidSpecError(f"{val=} must be a {bool}, got {type(key)}")


def validate_attribute(attr, flags):
    """
    Asserts that the given attribute is well-formed.
    """
    if not ATTR_KEYS_REQ <= set(attr.keys()):
        raise InvalidSpecError(f"Missing keys for {attr}: {ATTR_KEYS_REQ - set(attr.keys())}")
    if not set(attr.keys()) <= ATTR_KEYS_REQ | ATTR_KEYS_OPT:
        raise InvalidSpecError(f"Unrecognised keys for {attr}: {set(attr.keys()) - ATTR_KEYS_REQ - ATTR_KEYS_OPT}")

    if not isinstance(attr["name"], str):
        raise InvalidSpecError(f"{attr['name']=} must be a {str}, got {type(attr['name'])}")
    if not isinstance(attr["display_name"], str):
        raise InvalidSpecError(f"{attr['display_name']=} must be a {str}, got {type(attr['display_name'])}")
    if not isinstance(attr["type"], str):
        raise InvalidSpecError(f"{attr['type']=} must be a {str}, got {type(attr['type'])}")
    if not isinstance(attr["default"], str):
        raise InvalidSpecError(f"{attr['default']=} must be a {str}, got {type(attr['default'])}")

    # Verify that the flags attribute on the object, if it is exists, is correct
    if "flags" in attr:
        validate_flags_on_object(attr["flags"], flags)


def validate_component(comp, flags):
    """
    Asserts that the given component is well-formed.
    """
    if not COMP_KEYS_REQ <= set(comp.keys()):
        raise InvalidSpecError(f"Missing keys for {comp}: {COMP_KEYS_REQ - set(comp.keys())}")
    if not set(comp.keys()) <= COMP_KEYS_REQ | COMP_KEYS_OPT:
        raise InvalidSpecError(f"Unrecognised keys for {comp}: {set(comp.keys()) - COMP_KEYS_REQ | COMP_KEYS_OPT}")

    if not isinstance(comp["name"], str):
        raise InvalidSpecError(f"{comp['name']=} must be a {str}, got {type(comp['name'])}")
    if not isinstance(comp["display_name"], str):
        raise InvalidSpecError(f"{comp['display_name']=} must be a {str}, got {type(comp['display_name'])}")
    if not isinstance(comp["attributes"], list):
        raise InvalidSpecError(f"{comp['attributes']=} must be a {list}, got {type(comp['attributes'])}")

    # Verify that the flags attribute on the object, if it is exists, is correct
    if "flags" in comp:
        validate_flags_on_object(comp["flags"], flags)

    for attr in comp["attributes"]:
        validate_attribute(attr, flags)


def run(spec):
    """
    Runs the validator against the given spec, raising an exception if there
    is an error in the schema.
    """
    if set(spec.keys()) != SCHEMA_KEYS:
        raise InvalidSpecError(f"Incorrect keys for flag declaration, got {set(spec.keys())}, needed {SCHEMA_KEYS}")

    spec_flags = spec["flag_defaults"]
    if not isinstance(spec_flags, dict):
        raise InvalidSpecError(f"{spec_flags=} must be a {dict}, got {type(spec_flags)}")
    for flag, value in spec_flags.items():
        if not isinstance(flag, str):
            raise InvalidSpecError(f"{flag=} must be a {str}, got {type(flag)}")
        if not isinstance(value, bool):
            raise InvalidSpecError(f"{value=} must be a {bool}, got {type(value)}")

    spec_components = spec["components"]
    if not isinstance(spec_components, list):
        raise InvalidSpecError(f"{spec_components=} must be a {list}, got {type(spec_components)}")

    flags = set(spec_flags.keys())

    for comp in spec["components"]:
        validate_component(comp, flags)

    print("Schema Valid!")
