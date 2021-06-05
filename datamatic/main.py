"""
Command line parser for datamatic.
"""
import pathlib
import json
import importlib.util

from . import validator, generator, context, builtin


def load_spec(specfile: pathlib.Path):
    with specfile.open() as specfile_handle:
        spec = json.load(specfile_handle)
    fill_flag_defaults(spec)
    validator.run(spec)
    return spec


def discover(directory, method_register: context.MethodRegister):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main(method_register)


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

    method_register = context.MethodRegister()
    builtin.main(method_register)
    discover(directory, method_register)

    for file in directory.glob("**/*.dm.*"):
        generator.run(file, spec, method_register)

    print("Done!")