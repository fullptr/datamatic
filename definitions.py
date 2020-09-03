from datetime import datetime

def cpp_float(value):
    assert type(value) in {int, float}
    if "." not in str(value):
        return f"{value}.0f"
    return f"{value}f"

def default_cpp_repr(cpp_type, value):
    if cpp_type == "Maths::vec2":
        x, y = value
        return f'Maths::vec2{{{cpp_float(x)}, {cpp_float(y)}}}'

    if cpp_type == "Maths::vec3":
        x, y, z = value
        return f'Maths::vec3{{{cpp_float(x)}, {cpp_float(y)}, {cpp_float(z)}}}'

    if cpp_type in {"Maths::vec4", "Maths::quat"}:
        x, y, z, w = value
        return f'{cpp_type}{{{cpp_float(x)}, {cpp_float(y)}, {cpp_float(z)}, {cpp_float(w)}}}'

    if cpp_type == "bool":
        return "true" if value else "false"

    if cpp_type == "int":
        return str(value)

    if cpp_type == "float":
        return cpp_float(value)
    
    if cpp_type == "std::string":
        return f'"{value}"'

    if cpp_type == "std::queue<Maths::vec3>":  # TODO: Generalise this
        return "{}"

    return str(value)

def print_attr(attr):
    cpp_name = attr["Name"]
    cpp_type = attr["Type"]
    default = attr.get("Default")
    
    line = f"    {cpp_type} {cpp_name}"
    if default is not None:
        line += " = " + default_cpp_repr(cpp_type, default)
    line += ";"
    return line + "\n"

def generate(spec, output):

    out = f"// GENERATED FILE @ {datetime.now()}\n"
    out += "#pragma once\n"
    out += '#include "Maths.h"\n'
    out += "#include <queue>\n"
    out += "#include <string>\n\n"
    out += "namespace Sprocket{\n\n"

    out += "// Components\n"
    for component in spec["Components"]:
        out += f"struct {component['Name']}\n{{\n"
        for attr in component["Attributes"]:
            out += print_attr(attr)
        out += "};\n\n"

    out += "}\n"

    with open(output, "w") as outfile:
        outfile.write(out)