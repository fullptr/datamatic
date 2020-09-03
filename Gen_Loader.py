from datetime import datetime
import os.path as op

from . import definitions

def get_save_impl(spec):
    enums = spec["Enums"]
    out = ""
    for component in spec["Components"]:
        name = component["Name"]
        attrs = component["Attributes"]
        out += f"        if(entity.Has<{name}>()) {{\n"
        out += f"            const auto& c = entity.Get<{name}>();\n"
        out += f'            out << YAML::Key << "{name}" << YAML::BeginMap;\n'
        for attr in attrs:
            attr_name = attr["Name"]
            if attr.get("Savable", True):
                if attr["Type"] in enums:
                    out += f'            out << YAML::Key << "{attr_name}" << YAML::Value << static_cast<int>(c.{attr_name});\n'
                else:
                    out += f'            out << YAML::Key << "{attr_name}" << YAML::Value << c.{attr_name};\n'
        out += "            out << YAML::EndMap;\n"
        out += "        }\n"
    return out

def get_load_impl(spec):
    enums = spec["Enums"]
    out = ""
    for component in spec["Components"]:
        name = component["Name"]
        attrs = component["Attributes"]
        out += f'        if (auto spec = entity["{name}"]) {{\n'
        out += f'            {name} c;\n'
        for attr in attrs:
            attr_name = attr["Name"]
            attr_type = attr["Type"]
            if attr.get("Savable", True):
                if attr["Type"] in enums:
                    out += f'            c.{attr_name} = static_cast<{attr_type}>(spec["{attr_name}"].as<int>());\n'
                elif "Default" in attr:
                    out += f'            c.{attr_name} = spec["{attr_name}"] ? spec["{attr_name}"].as<{attr_type}>() : {definitions.default_cpp_repr(attr_type, attr["Default"])};\n'
                else:
                    out += f'            c.{attr_name} = spec["{attr_name}"].as<{attr_type}>();\n'
        out += f'            e.Add(c);\n'
        out += "        }\n"
    return out

def get_copy_impl(spec):
    out = ""
    for component in spec["Components"]:
        name = component["Name"]
        out += f"    if (entity.Has<{name}>()) {{\n"
        out += f"        e.Add<{name}>(entity.Get<{name}>());\n"
        out += "    }\n"
    return out

def generate(spec, output):
    template_file = op.join(op.dirname(op.abspath(__file__)), "Loader.dm.cpp")

    with open(template_file) as template:
        out = template.read()

    assert "#define TIME_STAMP" in out
    assert "#define LOADER_SAVE_IMPL" in out
    assert "#define LOADER_LOAD_IMPL" in out
    assert "#define LOADER_COPY_IMPL" in out

    out = out.replace("#define TIME_STAMP", f"// GENERATED FILE @ {datetime.now()}")
    out = out.replace("#define LOADER_SAVE_IMPL", get_save_impl(spec))
    out = out.replace("#define LOADER_LOAD_IMPL", get_load_impl(spec))
    out = out.replace("#define LOADER_COPY_IMPL", get_copy_impl(spec))

    with open(output, "w") as outfile:
        outfile.write(out)