"""
Command line parser for datamatic.
"""
import pathlib
import json

from . import validator, generator, method_register


def load_spec(specfile: pathlib.Path):
    with specfile.open() as specfile_handle:
        spec = json.load(specfile_handle)
    fill_flag_defaults(spec)
    validator.run(spec)
    return spec


def fill_flag_defaults(spec):
    defaults = spec["flag_defaults"]
    for comp in spec["components"]:
        comp_flags = comp.get("flags", {})
        comp["flags"] = {**defaults, **comp_flags}
        for attr in comp["attributes"]:
            attr_flags = attr.get("flags", {})
            attr["flags"] = {**defaults, **attr_flags}


def main(specfile: pathlib.Path, directory: pathlib.Path):
    """
    Entry point.
    """
    spec = load_spec(specfile)

    reg = method_register.MethodRegister()
    reg.load_builtins()
    reg.load_from_dmx(directory)

    for file in directory.glob("**/*.dm.*"):
        generator.run(file, spec, reg)

    print("Done!")