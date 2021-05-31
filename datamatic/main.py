"""
Command line parser for datamatic.
"""
import argparse
import pathlib
import json
import sys
import importlib.util

from . import validator, generator, context, builtin


def discover(directory, ctx: context.Context):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[spec.name] = module
        sys.modules[spec.name].main(ctx)


def fill_flag_defaults(spec):
    defaults = {flag["name"]: flag["default"] for flag in spec["flags"]}

    for comp in spec["components"]:
        comp_flags = comp.get("flags", {})
        comp["flags"] = {**defaults, **comp_flags}
        for attr in comp["attributes"]:
            attr_flags = attr.get("flags", {})
            attr["flags"] = {**defaults, **attr_flags}


def parse_args():
    """
    Read the command line.
    """
    parser = argparse.ArgumentParser(
        description="Given a component spec and a directory, scan the "
                    "directory for dm and dmx files and generate the "
                    "appropriate files"
    )

    parser.add_argument(
        "-s", "--spec",
        required=True,
        type=pathlib.Path,
        help="A path to the component spec JSON file"
    )

    parser.add_argument(
        "-d", "--dir",
        required=True,
        type=pathlib.Path,
        help="A path to the directory to scan for dm and dmx files"
    )

    return parser.parse_args()


def main(args):
    """
    Entry point.
    """
    ctx = context.Context()

    builtin.main(ctx)
    discover(args.dir, ctx)

    with args.spec.open() as specfile:
        spec = json.loads(specfile.read())

    fill_flag_defaults(spec)

    validator.run(spec, ctx)

    for file in args.dir.glob("**/*.dm.*"):
        generator.run(spec, file, ctx)

    print("Done!")