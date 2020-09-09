import json
import argparse
import pathlib

from Datamatic import Validator
from Datamatic import Generator
from Plugins import Lua, Inspector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--spec", required=True)
    parser.add_argument("-d", "--dir", required=True)
    return parser.parse_args()


def main(args):
    with open(args.spec) as specfile:
        spec = json.loads(specfile.read())

    Validator.run(spec)

    for file in pathlib.Path(args.dir).glob("**/*.dm.*"):
        Generator.run(spec, str(file))

    print("Done!")


if __name__ == "__main__":
    args = parse_args()
    main(args)