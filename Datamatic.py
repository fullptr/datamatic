"""
A tool for generating code based on a schema of Components.
"""
import json
import argparse
import pathlib
import importlib

from Datamatic import Plugins, Validator, Generator


def discover(directory):
    for file in pathlib.Path(directory).glob("**/*.dmx.py"):
        name = file.parts[-1].split(".")[0]
        spec = importlib.util.spec_from_file_location(name, str(file))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)


def parse_args():
    """
    Read the command line.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--spec", required=True)
    parser.add_argument("-d", "--dir", required=True)
    return parser.parse_args()


def main(args):
    """
    Entry point.
    """
    discover(args.dir)

    with open(args.spec) as specfile:
        spec = json.loads(specfile.read())

    Validator.run(spec)

    for file in pathlib.Path(args.dir).glob("**/*.dm.*"):
        Generator.run(spec, str(file))

    print("Done!")


if __name__ == "__main__":
    args = parse_args()
    main(args)