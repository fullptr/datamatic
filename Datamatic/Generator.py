import re
import inspect
from typing import Tuple, Literal
from dataclasses import dataclass
from functools import partial
from Datamatic.Plugins import Plugin
from Datamatic import Types


COMP_MATCH = re.compile(r"(\{\{Comp\..*?\}\})")
ATTR_MATCH = re.compile(r"(\{\{Attr\..*?\}\})")


@dataclass(frozen=True)
class Token:
    raw_string: str
    namespace: Literal["Comp", "Attr"]
    plugin_name: str
    function_name: str
    args: Tuple[str]


def parse_token_string(raw_string: str) -> Token:
    """
    Format:
    "{{" ("Comp"|"Attr") "." [plugin_name "."] function_name ["|" function_arg]* "}}"

    Examples:
    "{{Comp.conditional.if_nth_else|2|,|.}}"
    "{{Comp.Name}}"
    """
    assert raw_string.startswith("{{")
    assert raw_string.endswith("}}")

    *tokens, last_token = raw_string[2:-2].split(".")
    last_token, *args = last_token.split("|")
    tokens = *tokens, last_token
    args = tuple(args)

    namespace = tokens[0]
    if len(tokens) == 2:
        plugin_name = "builtin"
        function_name = tokens[1]
    elif len(tokens) == 3:
        plugin_name = tokens[1]
        function_name = tokens[2]
    else:
        raise RuntimeError(f"Invalid token {raw_string}")

    return Token(
        raw_string=raw_string,
        namespace=namespace,
        plugin_name=plugin_name,
        function_name=function_name,
        args=args
    )


def replace_token(matchobj, spec, obj):
    token = parse_token_string(matchobj.group(1))
    function = Plugin.get_function(token.namespace, token.plugin_name, token.function_name)

    # The plugin function may request extra information by having
    # certain parameters in the signature, here we now inspect the
    # function signature and bind any requested information.
    sig = inspect.signature(function)

    assert len(sig.parameters) > 0, f"Invalid function signature for {token}"
    
    #unknown_params = set(sig.parameters.keys()) - {token.namespace.lower(), "args", "spec"}
    #assert not unknown_params, f"Invalid parameter name(s) for {token}: {','.join(unknown_params)}"
    params = {}

    # If the function has a "args" parameter, bind the
    # args. If it doesn't assert that there were no args; if they
    # are specified then they must at least be requested (the
    # function may just ignore them).
    if "args" in sig.parameters:
        params["args"] = token.args
    else:
        assert len(token.args) == 0

    # If the function requests the spec, then pass it in.
    if "spec" in sig.parameters:
        params["spec"] = spec

    return function(obj, **params)


def get_attrs(comp, flags):
    attrs = comp["Attributes"]
    for key, value in flags.items():
        attrs = [x for x in attrs if x["Flags"][key] == value]
    return attrs


def get_comps(spec, flags):
    comps = spec["Components"]
    for key, value in flags.items():
        comps = [x for x in comps if x["Flags"][key] == value]
    return comps


def process_block(spec, block, flags):
    out = ""
    for comp in get_comps(spec, flags):
        for line in block:
            while "{{Comp." in line:
                line = COMP_MATCH.sub(partial(replace_token, spec=spec, obj=comp), line)

            if "{{Attr." in line:
                for attr in get_attrs(comp, flags):
                    newline = line
                    while "{{Attr." in newline:
                        newline = ATTR_MATCH.sub(partial(replace_token, spec=spec, obj=attr), newline)

                    out += newline + "\n"
            else:
                out += line + "\n"

    return out


def get_header(dst):
    if dst.suffix == ".lua":
        return "-- GENERATED FILE\n"
    return "// GENERATED FILE\n"


def parse_flag_val(val):
    assert val in {"true", "false"}
    return True if val == "true" else False


def parse_flags(flags):
    parsed_flags = {}
    for flag in flags:
        flag = flag.split("=")
        assert len(flag) == 2
        name = flag[0]
        val = parse_flag_val(flag[1])
        parsed_flags[name] = val
    return parsed_flags


def run(spec, src):
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
            if line == "#endif":
                out += process_block(spec, block, flags)
                in_block = False
                block = []
                flags = set()
            else:
                block.append(line)
        elif line.startswith("#ifdef DATAMATIC_BLOCK"):
            assert not in_block
            in_block = True
            flags = parse_flags(set(line.split()[2:]))
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
