"""
A module of utility functions to be used in both the core datamatic implmentation as
well as being made available to plugins.
"""


def flag_match(obj, flags):
    """
    Given a component or attribute, return true if it matches all of the given flags
    and False otherwise.
    """
    assert "flags" in obj
    return all(obj['flags'][key] == value for key, value in flags.items())


def filter_flags(obj_list, flags):
    """
    Given a list of components or attributes, and a dict of flags, return a list containing
    only the objects that match the flags.
    """
    return [obj for obj in obj_list if flag_match(obj, flags)]
