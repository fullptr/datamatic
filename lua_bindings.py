from datetime import datetime

def generate(spec, output):
    out = f"-- GENERATED FILE @ {datetime.now()}\n"
    for component in spec["Components"]:
        num_attrs = 0
        for attr in component["Attributes"]:
            if not attr.get("Scriptable", True):
                continue
            if attr["Type"] in {"Maths::vec4", "Maths::quat"}:
                num_attrs += 4
            elif attr["Type"] == "Maths::vec3":
                num_attrs += 3
            elif attr["Type"] == "Maths::vec2":
                num_attrs += 2
            else:
                num_attrs += 1

        name = component["Name"]
        if not component.get("Scriptable", True):
            continue
        out += f'{component["Name"]} = Class(function(self, '
        args = []
        for attr in component["Attributes"]:
            n = attr["Name"]
            if not attr.get("Scriptable", True):
                continue
            if attr["Type"] == "Maths::vec3":
                args.extend([f'{n}_x', f'{n}_y', f'{n}_z'])
            else:
                args.append(attr["Name"])
        out += ", ".join(args) + ")\n"
        for attr in component["Attributes"]:
            n = attr["Name"]
            if not attr.get("Scriptable", True):
                continue
            if attr["Type"] == "Maths::vec3":
                out += f'    self.{n} = Vec3({n}_x, {n}_y, {n}_z)\n'
            else:
                out += f'    self.{n} = {n}\n'
        out += "end)\n\n"

        out += f'function Get{name}()\n'
        pack = ", ".join([f'x{i}' for i in range(num_attrs)])
        out += "    " + pack + f" = Lua_Get{name}()\n"
        out += f'    return {name}({pack})\n'
        out += "end\n\n"

        out += f'function Set{name}(c)\n'
        out += f'    Lua_Set{name}('
        args = []
        for attr in component["Attributes"]:
            n = attr["Name"]
            if not attr.get("Scriptable", True):
                continue
            if attr["Type"] == "Maths::vec3":
                args.extend([f'c.{n}.x', f'c.{n}.y', f'c.{n}.z'])
            else:
                args.append(f'c.{attr["Name"]}')
        out += ", ".join(args)
        out += ')\n'
        out += "end\n\n"

    with open(output, "w") as outfile:
        outfile.write(out)