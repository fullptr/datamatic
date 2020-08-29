from datetime import datetime

header = """
#include "LuaComponents.h"
#include "LuaGlobals.h"
#include "Entity.h"
#include "Maths.h"
#include "Components.h"

#include <lua.hpp>
#include <cassert>

namespace Sprocket {
namespace {

template<typename T> int Lua_Has(lua_State* L)
{
    if (!CheckArgCount(L, 1)) { return luaL_error(L, "Bad number of args"); }

    Entity entity = *static_cast<Entity*>(lua_touserdata(L, 1));
    lua_pushboolean(L, entity.Has<T>());
    return 1;
}

}

void RegisterComponentFunctions(lua_State* L)
{
"""

middle = """}

namespace Lua {

"""

footer = """}
}
"""

def get_lua_pushfunc(attr):
    if attr["Type"] in {"int", "float"}:
        return "lua_pushnumber"
    if attr["Type"] == "bool":
        return "lua_pushboolean"
    return "lua_pushstring"

def get_lua_tofunc(attr):
    if attr["Type"] in {"int", "float"}:
        return "lua_tonumber"
    if attr["Type"] == "bool":
        return "lua_toboolean"
    return "lua_tostring"

def generate_header(spec, output):
    out = f"// GENERATED FILE @ {datetime.now()}\n"
    out += "class lua_State;\n\n"
    out += "namespace Sprocket {\n\n"
    out += "void RegisterComponentFunctions(lua_State* L);\n"
    out += "    // Register all the functions in this header with the given lua state.\n\n"
    out += "namespace Lua {\n\n"
    for component in spec["Components"]:
        if not component.get("Scriptable", True):
            continue
        name = component["Name"]
        out += f"int Get{name}(lua_State* L);\n"
        out += f"int Set{name}(lua_State* L);\n"
        out += f"int Add{name}(lua_State* L);\n\n"
    out += "}\n}"

    with open(output, "w") as outfile:
        outfile.write(out)

def generate_cpp(spec, output):
    out = f"// GENERATED FILE @ {datetime.now()}\n"
    out += header
    for component in spec["Components"]:
        if not component.get("Scriptable", True):
            continue
        name = component["Name"]
        out += f'    lua_register(L, "Lua_Get{name}", &Lua::Get{name});\n'
        out += f'    lua_register(L, "Lua_Set{name}", &Lua::Set{name});\n'
        out += f'    lua_register(L, "Lua_Add{name}", &Lua::Add{name});\n'
        out += f'    lua_register(L, "Has{name}", &Lua_Has<{name}>);\n\n'
    out += middle
    for component in spec["Components"]:
        name = component["Name"]
        attrs = component["Attributes"]

        num_attrs = 0
        for attr in attrs:
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

        if not component.get("Scriptable", True):
            continue
        
        # Getter
        out += f"int Get{name}(lua_State* L)\n{{\n"
        out += '    if (!CheckArgCount(L, 1)) { return luaL_error(L, "Bad number of args"); }\n'
        out += f'    Entity e = *static_cast<Entity*>(lua_touserdata(L, 1));\n'
        out += f'    assert(e.Has<{name}>());\n\n'
        out += f'    const auto& c = e.Get<{name}>();\n'

        count = 1
        for attr in attrs:
            if not attr.get("Scriptable", True):
                continue

            if attr["Type"] == "Maths::vec3":
                out += f'    lua_pushnumber(L, c.{attr["Name"]}.x);\n'
                count += 1
                out += f'    lua_pushnumber(L, c.{attr["Name"]}.y);\n'
                count += 1
                out += f'    lua_pushnumber(L, c.{attr["Name"]}.z);\n'
                count += 1
            elif attr["Type"] == "std::string":
                out += f'    lua_pushstring(L, c.{attr["Name"]}.c_str());\n'
                count += 1
            else:
                out += f'    {get_lua_pushfunc(attr)}(L, c.{attr["Name"]});\n'
                count += 1

        out += f'    return {num_attrs};\n'
        out += "}\n\n"

        # Setter
        out += f"int Set{name}(lua_State* L)\n{{\n"
        out += f'    if (!CheckArgCount(L, {num_attrs + 1})) {{ return luaL_error(L, "Bad number of args"); }}\n\n'
        out += f'    Entity e = *static_cast<Entity*>(lua_touserdata(L, 1));\n'
        out += f'    auto& c = e.Get<{name}>();\n'
        count = 2
        for attr in attrs:
            if not attr.get("Scriptable", True):
                continue

            if attr["Type"] == "Maths::vec3":
                out += f'    c.{attr["Name"]}.x = (float)lua_tonumber(L, {count});\n'
                count += 1
                out += f'    c.{attr["Name"]}.y = (float)lua_tonumber(L, {count});\n'
                count += 1
                out += f'    c.{attr["Name"]}.z = (float)lua_tonumber(L, {count});\n'
                count += 1
            elif attr["Type"] == "std::string":
                out += f'    c.{attr["Name"]} = std::string({get_lua_tofunc(attr)}(L, {count}));\n'
                count += 1
            else:
                out += f'    c.{attr["Name"]} = ({attr["Type"]}){get_lua_tofunc(attr)}(L, {count});\n'
                count += 1
        out += "    return 0;\n"
        out += "}\n\n"

        #Adder
        out += f"int Add{name}(lua_State* L)\n{{\n"
        out += f'    if (!CheckArgCount(L, {num_attrs + 1})) {{ return luaL_error(L, "Bad number of args"); }}\n\n'
        out += f'    Entity e = *static_cast<Entity*>(lua_touserdata(L, 1));\n'
        out += f'    assert(!e.Has<{name}>());\n\n'
        out += f'    {name} c;\n'
        count = 2
        for attr in attrs:
            if not attr.get("Scriptable", True):
                continue

            if attr["Type"] == "Maths::vec3":
                out += f'    c.{attr["Name"]}.x = (float)lua_tonumber(L, {count});\n'
                count += 1
                out += f'    c.{attr["Name"]}.y = (float)lua_tonumber(L, {count});\n'
                count += 1
                out += f'    c.{attr["Name"]}.z = (float)lua_tonumber(L, {count});\n'
                count += 1
            elif attr["Type"] == "std::string":
                out += f'    c.{attr["Name"]} = std::string({get_lua_tofunc(attr)}(L, {count}));\n'
                count += 1
            else:
                out += f'    c.{attr["Name"]} = ({attr["Type"]}){get_lua_tofunc(attr)}(L, {count});\n'
                count += 1
        out += "    e.Add(c);\n"
        out += "    return 0;\n"
        out += "}\n\n"
    out += footer

    with open(output, "w") as outfile:
        outfile.write(out)