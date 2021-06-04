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


def discover(directory, ctx: context.Context):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main(ctx)


def fill_flag_defaults(spec):
    defaults = {flag["name"]: flag["default"] for flag in spec["flags"]}

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

    ctx = context.Context(spec)
    builtin.main(ctx)
    discover(directory, ctx)

    for file in directory.glob("**/*.dm.*"):
        generator.run(file, ctx)

    print("Done!")