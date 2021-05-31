"""
Command line parser for datamatic.
"""
import argparse
import pathlib
import json
import sys
import importlib.util

from . import validator, generator, api, builtin


def discover(type_parser: api.TypeParser, plugin_list: api.PluginList, directory):
    for file in directory.glob("**/*.dmx.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[spec.name] = module
        sys.modules[spec.name].main(type_parser, plugin_list)


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
    type_parser = api.TypeParser()
    plugin_list = api.PluginList()

    builtin.main(type_parser, plugin_list)
    discover(type_parser, plugin_list, args.dir)

    with args.spec.open() as specfile:
        spec = json.loads(specfile.read())

    fill_flag_defaults(spec)

    validator.run(spec, plugin_list)

    for file in args.dir.glob("**/*.dm.*"):
        generator.run(spec, file, type_parser, plugin_list)

    print("Done!")