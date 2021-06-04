import re
import pathlib
from typing import Tuple, Literal, Optional
from dataclasses import dataclass, field
from functools import partial
import parse


TOKEN = re.compile(r"\{\{(.*?)\}\}")


@dataclass(frozen=True)
class Token:
    namespace: Literal["Comp", "Attr"]
    function_name: str
    args: Tuple[str]
    raw_string: Optional[str] = field(default=None, compare=False)


def parse_token_string(raw_string: str) -> Token:
    """
    Format:
    ("Comp"|"Attr") "::" function_name ["(" <args> ")"]

    Examples:
    "Comp::conditional.if_nth_else(2|,|.)"
    "Comp::name"
    """
    try:
        namespace, rest = raw_string.split("::")
        if result := parse.parse("{}({})", rest):
            function_name = result[0]
            args = tuple(arg.strip() for arg in result[1].split("|"))
        elif result := parse.parse("{}()", rest):
            function_name = result[0]
            args = tuple()
        else:
            function_name = rest
            args = tuple()
    except ValueError as e:
        raise RuntimeError(f"Error: {e}, {raw_string=}") from e

    return Token(
        namespace=namespace,
        function_name=function_name,
        args=args,
        raw_string=raw_string,
    )


def replace_token(matchobj, obj, context):
    """
    Parse the replacement token in the matchobj to figure out the namespace, function name
    and any args provided. Get the function and then pass the comp/attr and any extra arguments.
    """
    token = parse_token_string(matchobj.group(1))
    function = context.get(token.namespace, token.function_name)
    return function(obj, *token.args)


def flag_filter(objects, flags):
    for obj in objects:
        if all(obj['flags'][key] == value for key, value in flags.items()):
            yield obj


def process_block(block, flags, context):
    out = ""
    for comp in flag_filter(context.spec["components"], flags):
        for line in block:
            while "{{Comp::" in line:
                line = TOKEN.sub(partial(replace_token, obj=comp, context=context), line)

            if "{{Attr::" in line:
                for attr in flag_filter(comp["attributes"], flags):
                    newline = line
                    while "{{Attr::" in newline:
                        newline = TOKEN.sub(partial(replace_token, obj=attr, context=context), newline)

                    out += newline + "\n"
            else:
                out += line + "\n"

    return out


def get_header(dst):
    if dst.suffix == ".lua":
        return "-- GENERATED FILE\n"
    return "// GENERATED FILE\n"


def parse_flag_val(val):
    valid_vals = {"true", "false"}
    if val not in valid_vals:
        raise RuntimeError(f"Invalid flag value: {val}, must be one of {valid_vals}")
    return True if val == "true" else False


def parse_flags(flags):
    parsed_flags = {}
    for flag in flags:
        flag = flag.split("=")
        if len(flag) != 2:
            raise RuntimeError(f"In correct number of tokens in flag {flag}, must have exactly one '='")
        name = flag[0]
        val = parse_flag_val(flag[1])
        parsed_flags[name] = val
    return parsed_flags


def run(src, context):
    dst = src.parent / src.name.replace(".dm.", ".")

    with src.open() as srcfile:
        lines = srcfile.readlines()

    in_block = False
    block = []
    flags = set()
    out = get_header(dst)
    for line in lines:
        line = line.rstrip()

        if in_block:
            if line.startswith("DATAMATIC_BEGIN"):
                raise RuntimeError("Tried to begin a datamatic block while in another, cannot be nested")
            if line.startswith("DATAMATIC_END"):
                out += process_block(block, flags, context)
                in_block = False
                block = []
                flags = set()
            else:
                block.append(line)
        elif line.startswith("DATAMATIC_BEGIN"):
            in_block = True
            flags = parse_flags(set(line.split()[1:]))
        else:
            out += line + "\n"

    if dst.exists():
        with dst.open() as dstfile:
            if dstfile.read() == out:
                print(f"No change to {dst}")
                return

    with dst.open("w") as dstfile:
        dstfile.write(out)

    print(f"Generated file {dst}")
