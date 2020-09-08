from datetime import datetime
from functools import partial
import os.path as op
import re

from . import definitions

COMP_MATCH = re.compile(r"(\{\{Comp\.[a-zA-Z \.\(\)]*\}\})")
ATTR_MATCH = re.compile(r"(\{\{Attr\.[a-zA-Z \.\(\)]*\}\})")

class CompHandle:
    def __init__(self, comp):
        self.comp = comp

    def __getattr__(self, attr):
        if attr in self.comp:
            value = self.comp[attr]
            if isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, str):
                return value
        raise RuntimeError(f"Accessing invalid attr {attr}")

class Attr:
    pass

def comp_repl(matchobj, comp):
    symbols = matchobj.group(1)[2:-2].split(".")
    handle = CompHandle(comp)
    assert len(symbols) == 2
    first, second = symbols
    assert first == "Comp" 
    return getattr(handle, second)

def get_attrs(comp, flags):
    attrs = comp["Attributes"] 
    if "SAVABLE" in flags:
        return (attr for attr in attrs if attr.get("Savable", True))
    if "SCRIPTABLE" in flags:
        return (attr for attr in attrs if attr.get("Scriptable", True))
    else:
        return attrs


def fill_attribute(attr, line):
    line = line.replace("{{Attr.Name}}", attr["Name"])
    line = line.replace("{{Attr.DisplayName}}", attr["DisplayName"])
    line = line.replace("{{Attr.Type}}", attr["Type"])

    line = line.replace(
        "{{Attr.Default}}",
        definitions.default_cpp_repr(attr["Type"], attr["Default"])
    )

    assert "{{Attr." not in line, line
    return line


def fill_component(comp, line):
    while "{{Comp." in line:
        line = COMP_MATCH.sub(partial(comp_repl, comp=comp), line)
    #line = line.replace("{{Comp.Name}}", comp["Name"])
    #line = line.replace("{{Comp.DisplayName}}", comp["DisplayName"])

    #line = line.replace(
    #    "{{Comp.Scriptable}}",
    #    "true" if comp.get("Scriptable", True) else "false"
    #)

    return line


def process_block(spec, block, flags):
    out = ""
    for comp in spec["Components"]:
        for line in block:
            while "{{Comp." in line:
                line = COMP_MATCH.sub(partial(comp_repl, comp=comp), line)

            if "{{Attr." in line:
                for attr in get_attrs(comp, flags):
                    out += fill_attribute(attr, line) + "\n"
            else:
                out += line + "\n"

    return out

def generate(spec, src, dst):
    
    with open(src) as srcfile:
        lines = srcfile.readlines()

    in_block = False
    block = []
    flags = set()
    out = "// GENERATED FILE\n"
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