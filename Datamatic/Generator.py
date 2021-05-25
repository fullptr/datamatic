import re
import inspect
from functools import partial
from Datamatic.Plugins import Plugin
from Datamatic import Types


COMP_MATCH = re.compile(r"(\{\{Comp\.[a-zA-Z \.\(\)]*\}\})")
ATTR_MATCH = re.compile(r"(\{\{Attr\.[a-zA-Z \.\(\)]*\}\})")


def comp_repl(matchobj, spec, comp):
    """
    Either a standard access:
    "Comp.<trait_name>"

    Or a plugin call with optional args:
    "Comp.<plugin_name>.<function_name>(|<argument>)*"
    """
    symbols = matchobj.group(1)[2:-2].split(".")
    assert len(symbols) in {2, 3}

    if len(symbols) == 2:
        namespace, trait = symbols
        assert namespace == "Comp" 

        if value := comp.get(trait):
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, str):
                return value
        raise RuntimeError(f"Accessing invalid attr {trait}")

    elif len(symbols) == 3:
        namespace, plugin_name, trait_and_args = symbols
        trait, *args = trait_and_args.split("|")
        assert namespace == "Comp"

        plugin = Plugin.get(plugin_name)
        func = getattr(plugin, trait)
        assert func.__type == "Comp"

        # The plugin function may request extra information by having
        # certain parameters in the signature, here we now inspect the
        # function signature and bind any requested information.
        sig = inspect.signature(func)

        assert len(sig.parameters) > 0, f"Invalid function signature for {plugin_name}.{trait}, requires a 'comp' parameter"
        
        unknown_params = set(sig.parameters.keys()) - {"comp", "args", "spec"}
        assert not unknown_params, f"Invalid parameter name(s) for {plugin_name}.{trait}: {','.join(unknown_params)}"
        params = {}

        # If the function has a "args" parameter, bind the
        # args. If it doesn't assert that there were no args; if they
        # are specified then they must at least be requested (the
        # function may just ignore them).
        if "args" in sig.parameters:
            params["args"] = args
        else:
            assert len(args) == 0

        # If the function requests the spec, then pass it in.
        if "spec" in sig.parameters:
            params["spec"] = spec

        return func(comp, **params)

    else:
        raise RuntimeError(f"Invalid line {symbols}")


def attr_repl(matchobj, spec, attr):
    symbols = matchobj.group(1)[2:-2].replace(":", ".").split(".")
    assert len(symbols) in {2, 3}

    if len(symbols) == 2:
        namespace, trait = symbols
        assert namespace == "Attr" 

        if trait == "Default":
            cls = Types.get(attr["Type"])
            return repr(cls(attr[trait]))
        
        if value := attr.get(trait):
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, str):
                return value
        raise RuntimeError(f"Accessing invalid attr {trait}")

    elif len(symbols) == 3:
        namespace, plugin_name, trait = symbols
        assert namespace == "Attr"

        plugin = Plugin.get(plugin_name)
        func = getattr(plugin, trait)
        assert func.__type == "Attr"

        # The function can either accept 1 argument or 2. The first
        # argument is the current component. The optional second is the
        # entire component spec
        sig = inspect.signature(func)
        sig_len = len(sig.parameters)
        assert sig_len in {1, 2}
        if sig_len == 1:
            return func(attr)
        return func(attr, spec)
    
    else:
        raise RuntimeError(f"Invalid line {symbols}")


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
                line = COMP_MATCH.sub(partial(comp_repl, spec=spec, comp=comp), line)

            if "{{Attr." in line:
                for attr in get_attrs(comp, flags):
                    newline = line
                    while "{{Attr." in newline:
                        newline = ATTR_MATCH.sub(partial(attr_repl, spec=spec, attr=attr), newline)
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
