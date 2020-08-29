from datetime import datetime

def generate(spec, output):
    out = f"-- GENERATED FILE @ {datetime.now()}\n"
    for component in spec["Components"]:
        num_attrs = 0
        constructor_sig = []
        for attr in component["Attributes"]:
            if not attr.get("Scriptable", True):
                continue
            if attr["Type"]  == "Maths::vec4":
                constructor_sig.append(f"Vec4(x{num_attrs}, x{num_attrs+1}, x{num_attrs+2}, x{num_attrs+3})")
                num_attrs += 4
            elif attr["Type"] == "Maths::vec3":
                constructor_sig.append(f"Vec3(x{num_attrs}, x{num_attrs+1}, x{num_attrs+2})")
                num_attrs += 3
            elif attr["Type"] == "Maths::vec2":
                constructor_sig.append(f"Vec3(x{num_attrs}, x{num_attrs+1})")
                num_attrs += 2
            else:
                constructor_sig.append(f"x{num_attrs}")
                num_attrs += 1

        name = component["Name"]
        if not component.get("Scriptable", True):
            continue
        out += f'{component["Name"]} = Class(function(self, '
        
        args = [attr["Name"] for attr in component["Attributes"] if attr.get("Scriptable", True)]
        out += ", ".join(args) + ")\n"

        for attr in component["Attributes"]:
            if attr.get("Scriptable", True):
                n = attr["Name"]
                out += f'    self.{n} = {n}\n'
        out += "end)\n\n"

        out += f'function Get{name}(entity)\n'
        pack = ", ".join([f'x{i}' for i in range(num_attrs)])
        out += "    " + pack + f" = Lua_Get{name}(entity)\n"
        out += f'    return {name}({", ".join(constructor_sig)})\n'
        out += "end\n\n"

        out += f'function Set{name}(entity, c)\n'
        out += f'    Lua_Set{name}(entity, '
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

        out += f'function Add{name}(entity, c)\n'
        out += f'    Lua_Add{name}(entity, '
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