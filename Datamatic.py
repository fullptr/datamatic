"""
A tool for generating code based on a schema of components.
"""
import json
import argparse
import pathlib
import sys
import importlib.util
from Datamatic import Validator, Generator


def discover(directory):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)


def fill_flag_defaults(spec):
    defaults = {flag["name"]: flag["default"] for flag in spec["flags"]}

    for comp in spec["components"]:
        comp_flags = comp.get("flags", {})
        comp["flags"] = {**defaults, **comp_flags}
        for attr in comp["Attributes"]:
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
    discover(args.dir)

    with args.spec.open() as specfile:
        spec = json.loads(specfile.read())

    fill_flag_defaults(spec)

    Validator.run(spec)

    for file in args.dir.glob("**/*.dm.*"):
        Generator.run(spec, file)

    print("Done!")


if __name__ == "__main__":
    args = parse_args()
    main(args)