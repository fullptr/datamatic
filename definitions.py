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

    return "{}"