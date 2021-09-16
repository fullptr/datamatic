"""
A tool for generating code based on a schema of components.
"""
import argparse
import pathlib
from datamatic import main

inplace_help = """\
Scans the given directory, importing all dmx files it finds and producing source files
that sit alongside the template files.
"""

package_help = """\
Given a source dir and a destination dir, import all dmx files found in the source dir, and make
a copy of the entire source dir saved as the destination. Template files are replaced by the
rendered source code and all datamatic files are removed. Any non-template files in the source
are copied over.
"""

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

    subparsers = parser.add_subparsers(dest="command")

    inplace = subparsers.add_parser("inplace", help=inplace_help)
    inplace.add_argument(
        "--dir",
        required=True,
        type=pathlib.Path,
        help="A path to the directory to scan for dm and dmx files"
    )

    package = subparsers.add_parser("package", help=package_help)
    package.add_argument(
        "--src",
        required=True,
        type=pathlib.Path,
        help="A path to the source directory that contains dm, dmx and regular files"
    )

    package.add_argument(
        "--dst",
        required=True,
        type=pathlib.Path,
        help="A path to the dest directory that will contain all rendered files"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    spec = args.spec
    if args.command == "inplace":
        main.main_inplace(spec, args.dir)
    else:
        main.main_package(spec, args.src, args.dst)