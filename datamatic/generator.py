import re
from typing import Tuple, Literal, Optional
from dataclasses import dataclass
from functools import partial
import parse
import ast


TOKEN = re.compile(r"\{\{(.*?)\}\}")


class GeneratorError(Exception):
    def __init__(self, file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = file

    def __str__(self):
        return f"[{self.file}] {super().__str__()}"


@dataclass
class Context:
    spec: list
    comp: dict
    attr: Optional[dict]  # Only populated for attrmethods

    @property
    def namespace(self):
        return "Attr" if self.attr is not None else "Comp"


@dataclass(frozen=True)
class Token:
    namespace: Literal["Comp", "Attr"]
    function_name: str
    args: Tuple[str]


def parse_token_string(file, raw_string: str) -> Token:
    """
    Format:
    ("Comp"|"Attr") "::" function_name ["(" <args> ")"]

    Examples:
    Comp::if_nth_else(2, ",", ".")
    Comp::name
    """
    try:
        namespace, rest = raw_string.split("::")
    except ValueError as e:
        raise GeneratorError(file, f"Invalid token: {e}, {raw_string=}")

    if result := parse.parse("{}({})", rest):
        function_name = result[0]
        try:
            args = tuple(ast.literal_eval(result[1]))
        except SyntaxError:
            raise GeneratorError(file, f"Could not parse arg list ({result[1]}) for function {function_name}")
    elif result := parse.parse("{}()", rest):
        function_name = result[0]
        args = tuple()
    else:
        function_name = rest
        args = tuple()

    return Token(
        namespace=namespace,
        function_name=function_name,
        args=args,
    )
    

def apply_flags_to_spec(spec, flags):
    """
    Returns a copy of the component list but with the given flags applied; any component or
    attribute that doesn't match the given flags are omitted.
    """
    # If we are not using flags, then no filtering is required.
    if "flag_defaults" not in spec:
        return spec

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


def replace_token(matchobj, file, comp, attr, spec, method_register):
    """
    Parse the replacement token in the matchobj to figure out the namespace, function name
    and any args provided. Get the function and then pass the comp/attr and any extra arguments.
    """
    token = parse_token_string(file, matchobj.group(1))
    function = method_register.get(token.namespace, token.function_name)
    ctx = Context(spec=spec, comp=comp, attr=attr)
    return function(ctx, *token.args)


def process_block(file, block, flags, spec, method_register):
    out = ""
    filtered_spec = apply_flags_to_spec(spec, flags)
    for comp in filtered_spec:
        for line in block:
            had_comp_substitute = False
            while "{{Comp::" in line:
                had_comp_substitute = True
                line = TOKEN.sub(partial(replace_token, file=file, comp=comp, attr=None, spec=filtered_spec, method_register=method_register), line)

            if "{{Attr::" in line:
                for attr in comp["attributes"]:
                    newline = line
                    had_attr_substitute = False
                    while "{{Attr::" in newline:
                        had_attr_substitute = True
                        newline = TOKEN.sub(partial(replace_token, file=file, comp=comp, attr=attr, spec=filtered_spec, method_register=method_register), newline)

                    if not (had_attr_substitute and line == ""): # If a symbol substitution resulted in an empty line, don't add it
                        out += newline + "\n"
            else:
                if not (had_comp_substitute and line == ""):  # If a symbol substitution resulted in an empty line, don't add it
                    out += line + "\n"

    return out


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
        name, value = flag
        parsed_flags[name] = parse_flag_val(value)
    return parsed_flags


def run(src, spec, method_register):
    dst = src.parent / src.name.replace(".dm.", ".")

    with src.open() as srcfile:
        lines = srcfile.readlines()

    in_block = False
    block = []
    flags = set()
    out = ""
    for line in lines:
        line = line.rstrip()

        if in_block:
            if line.startswith("DATAMATIC_BEGIN"):
                raise RuntimeError("Tried to begin a datamatic block while in another, cannot be nested")
            if line.startswith("DATAMATIC_END"):
                out += process_block(src, block, flags, spec, method_register)
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
                return False

    with dst.open("w") as dstfile:
        dstfile.write(out)

    print(f"Generated file {dst}")
    return True
