import re
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
    

def apply_flags_to_spec(spec, flags):
    """
    Returns a copy of the component list but with the given flags applied; any component or
    attribute that doesn't match the given flags are omitted.
    """
    components = []
    for comp in spec["components"]:
        if all(comp['flags'][key] == value for key, value in flags.items()):
            new_comp = {"attributes": []}
            for key, value in comp.items():
                if key in {"flags", "attributes"}:
                    continue
                new_comp[key] = value
            for attr in comp["attributes"]:
                if all(attr['flags'][key] == value for key, value in flags.items()):
                    new_attr = {}
                    for key, value in attr.items():
                        if key in {"flags"}:
                            continue
                        new_attr[key] = value
                    new_comp["attributes"].append(new_attr)
            components.append(new_comp)
    return components


def replace_token(matchobj, obj, spec, method_register):
    """
    Parse the replacement token in the matchobj to figure out the namespace, function name
    and any args provided. Get the function and then pass the comp/attr and any extra arguments.
    """
    token = parse_token_string(matchobj.group(1))
    function = method_register.get(token.namespace, token.function_name)
    return function(spec, obj, *token.args)


def process_block(block, flags, spec, method_register):
    out = ""
    filtered_spec = apply_flags_to_spec(spec, flags)
    for comp in filtered_spec:
        for line in block:
            while "{{Comp::" in line:
                line = TOKEN.sub(partial(replace_token, obj=comp, spec=filtered_spec, method_register=method_register), line)

            if "{{Attr::" in line:
                for attr in comp["attributes"]:
                    newline = line
                    while "{{Attr::" in newline:
                        newline = TOKEN.sub(partial(replace_token, obj=attr, spec=filtered_spec, method_register=method_register), newline)

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


def run(src, spec, method_register):
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
                out += process_block(block, flags, spec, method_register)
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
