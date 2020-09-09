"""
A tool for generating code based on a schema of Components.
"""
import json
import argparse
import pathlib
import sys
import importlib.util
from Datamatic import Plugins, Validator, Generator


def discover(directory):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)


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

    Validator.run(spec)

    for file in args.dir.glob("**/*.dm.*"):
        Generator.run(spec, file)

    print("Done!")


if __name__ == "__main__":
    args = parse_args()
    main(args)