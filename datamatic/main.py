"""
Command line parser for datamatic.
"""
import os
import pathlib
import json
import shutil

from . import validator, generator, method_register


def load_spec(specfile: pathlib.Path):
    with specfile.open() as specfile_handle:
        spec = json.load(specfile_handle)
    fill_flag_defaults(spec)
    validator.run(spec)
    return spec


def fill_flag_defaults(spec):
    if "flag_defaults" not in spec:
        return
        
    defaults = spec["flag_defaults"]
    for comp in spec["components"]:
        comp_flags = comp.get("flags", {})
        comp["flags"] = {**defaults, **comp_flags}
        for attr in comp["attributes"]:
            attr_flags = attr.get("flags", {})
            attr["flags"] = {**defaults, **attr_flags}


def main_inplace(specfile: pathlib.Path, directory: pathlib.Path):
    """
    Entry point for the inplace tool.
    """
    spec = load_spec(specfile)

    reg = method_register.MethodRegister()
    reg.load_builtins()
    reg.load_from_dmx(directory)

    count = 0
    for srcfile in directory.glob("**/*.dm.*"):
        dstfile = srcfile.parent / srcfile.name.replace(".dm.", ".")
        if generator.run(srcfile, dstfile, spec, reg):
            count += 1

    print(f"Done! Generated {count} files")
    return count


def main_package(specfile: pathlib.Path, src: pathlib.Path, dst: pathlib.Path):
    """
    Entry point for the package tool.
    """
    spec = load_spec(specfile)

    reg = method_register.MethodRegister()
    reg.load_builtins()
    reg.load_from_dmx(src)

    if dst.exists():
        print("Deleting old dst directory")
        shutil.rmtree(str(dst))
    print("Creating new dst directory")
    os.mkdir(str(dst))

    count = 0
    plugins = set(src.glob("**/*.dmx.py"))
    templates = set(src.glob("**/*.dm.*"))
    for srcfile in src.glob("**/*"):
        if srcfile in plugins:
            continue  # Ignore plugins

        if srcfile in templates:
            dstfile = dst / srcfile.name.replace(".dm.", ".")
            if generator.run(srcfile, dstfile, spec, reg):
                count += 1
        else:
            dstfile = dst / srcfile.name
            shutil.copy(srcfile, dstfile)

    print(f"Done! Generated {count} files")
    return count
