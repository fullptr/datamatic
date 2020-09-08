from datetime import datetime
from functools import partial
import os.path as op
import re

from . import definitions
from Datamatic.Plugin import Plugin

COMP_MATCH = re.compile(r"(\{\{Comp\.[a-zA-Z \.\(\)]*\}\})")
ATTR_MATCH = re.compile(r"(\{\{Attr\.[a-zA-Z \.\(\)]*\}\})")

def comp_repl(matchobj, comp, flags):
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
        namespace, plugin_name, trait = symbols
        assert namespace == "Comp"

        plugin = Plugin.get(plugin_name)
        func = getattr(plugin, trait)
        assert func.__type == "Comp"
        return func(comp, flags)

    else:
        raise RuntimeError(f"Invalid line {symbols}")

def attr_repl(matchobj, attr, flags):
    symbols = matchobj.group(1)[2:-2].split(".")
    assert len(symbols) in {2, 3}

    if len(symbols) == 2:
        namespace, trait = symbols
        assert namespace == "Attr" 

        if trait == "Default":
            return definitions.default_cpp_repr(attr["Type"], attr[trait])
        
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
        return func(attr, flags)
    
    else:
        raise RuntimeError(f"Invalid line {symbols}")


def get_attrs(comp, flags):
    attrs = comp["Attributes"] 
    if "SAVABLE" in flags:
        attrs = [x for x in attrs if x.get("Savable", True)]
    if "SCRIPTABLE" in flags:
        attrs = [x for x in attrs if x.get("Scriptable", True)]
    return attrs

def get_comps(spec, flags):
    comps = spec["Components"]
    if "SCRIPTABLE" in flags:
        comps = [x for x in comps if x.get("Scriptable", True)]
    return comps

def process_block(spec, block, flags):
    out = ""
    for comp in get_comps(spec, flags):
        for line in block:
            while "{{Comp." in line:
                line = COMP_MATCH.sub(partial(comp_repl, comp=comp, flags=flags), line)

            if "{{Attr." in line:
                for attr in get_attrs(comp, flags):
                    newline = line
                    while "{{Attr." in newline:
                        newline = ATTR_MATCH.sub(partial(attr_repl, attr=attr, flags=flags), newline)
                    out += newline + "\n"
            else:
                out += line + "\n"

    return out

def get_header(dst):
    if dst.endswith(".lua"):
        return "-- GENERATED FILE\n"
    return "// GENERATED FILE\n"

def generate(spec, src):
    dst = src.replace(".dm.", ".")
    print(f"Generating file {dst}")
    
    with open(src) as srcfile:
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
            flags = set(line.split()[2:])
        else:
            out += line + "\n"

    with open(dst, "w") as dstfile:
        dstfile.write(out)