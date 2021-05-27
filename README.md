# Datamatic
A python package for generating C++ and Lua source code.

## Motivation
As part of another project, I am using an [Entity Component System](https::github.com/MagicLemms/apecs). However, I kept finding areas where I needed to loop over all component types to implement logic, for example, exposing components to Lua, displaying them withing an ImGui editor window, and writing serialisation code. This made adding new components very cumbersome, as there would be several different areas of the code that would need updating.

With this tool, components can be defined in a json file, and C++ and Lua source templates can be provided which will be used to generate the actual files with the components added in. With this approach, adding a new component is trivial; I just add it to the json component spec and rerun the tool and all the source code will be generated.

## Usage
Firstly, you must create a component spec json file. As a basic example (flags, custom types and other features explained later):
```json
{
    "flags": [],
    "components": [
        {
            "name": "NameComponent",
            "display_name": "Name",
            "attributes": [
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "std::string",
                    "default": "Entity"
                }
            ]
        },
        {
            "name": "HealthComponent",
            "display_name": "Health",
            "attributes": [
                {
                    "name": "current_health",
                    "display_name": "Current Health",
                    "type": "float",
                    "default": 100.0
                },
                {
                    "name": "max_health",
                    "display_name": "Maximum Health",
                    "type": "float",
                    "default": 100.0
                }
            ]
        },
        {
            "name": "TransformComponent",
            "display_name": "Transform",
            "attributes": [
                {
                    "name": "position",
                    "display_name": "Position",
                    "type": "glm::vec3",
                    "default": [0.0, 0.0, 0.0]
                },
                {
                    "name": "orientation",
                    "display_name": "Orientation",
                    "type": "glm::quat",
                    "default": [0.0, 0.0, 0.0, 1.0]
                },
                {
                    "name": "scale",
                    "display_name": "Scale",
                    "type": "glm::vec3",
                    "default": [1.0, 1.0, 1.0]
                }
            ]
        }
    ]
}
```
For a full description of what a valid schema is, see [Validator.py](Datamatic/Validator.py). Next, create some template files. These can exist anywhere in your repository and must have a `.dm.*` suffix. When datamatic is ran, the generated file will be created in the same location without the `.dm`. For example, if you have `components.dm.h`, a `components.h` file will be created. An example of a template file is:
```cpp
#include <glm/glm.hpp>

#ifdef DATAMATIC_BLOCK
struct {{Comp.name}}
{
    {{Attr.type}} {{Attr.name}} = {{Attr.default}};
};

#endif
```
Notice a few things
* A block of template code uses C++'s `#ifdef` and `#endif` macros with `DATAMATIC_BLOCK` as the symbol. This symbol should not be defined; the only reason I use this rather than custom syntax is so that C++ syntax highlighting can still work on the template files without raising errors. Since the `DATAMATIC_BLOCK` symbol is not defined, the template code is ignored by the syntax highlighter (at least in VS Code).
* Attributes are accessed via the double curly brace notation. Attributes are in one of two namespaces, `Comp` and `Attr`. The block is copied for each of the components in the spec, and everywhere the `Comp` namespace is used is substituted for the current component. The `Attr` namespace works differently. If a line has an `Attr` symbol, that line is duplicated for each attribute in the component, so it isn't necessary to specify a loop when specifying attributes.

Running Datamatic is very simple. It has no external dependencies so can just be cloned and ran on a repository as follows:
```bash
python Datamatic.py --spec <path/to/json/spec> --dir <path/to/project/root>
```

With the above spec and template, the following would be generated:
```cpp
#include <glm/glm.hpp>

struct NameComponent
{
    std::string name = "Entity";
};

struct HealthComponent
{
    float current_health = 100.0f;
    float maximum_health = 100.0f;
};

struct TransformComponent
{
    glm::vec3 position = {0.0, 0.0, 0.0};
    glm::quat orientation = {0.0, 0.0, 0.0, 1.0};
    glm::vec3 scale = {1.0, 1.0, 1.0};
};

```

## Flags
You may have noticed in the spec file above that it contained a `flags` top level attribute. Flags provide a way to set boolean flags on components and attributes which can be used to ignore certain components/attributes in template blocks. For example, when saving a game, we may not want the health of entities to be saved (not a great example but it work to demonstrate the point). We can declare a flag called `SERIALISABLE` in the spec file in the following way
```json
{
    "flags": [
        {
            "name": "SERIALISABLE",
            "default": true
        }
    ],
    "components": [
        {
            "name": "HealthComponent",
            "display_name": "Health",
            "flags": {
                "SERIALISABLE": false
            },
            "attributes": [ ... ]
        },
        ...
    ]
}
```
If a flag is not specified for a component or attribute, the default value is used. Then the serialisation code template may look like
```cpp
#ifdef DATAMATIC_BLOCK SERIALISABLE=true
    {{Comp.serialise.save_function}};
    {{Comp.serialise.load_function}};
#endif
```
Flags are passed on the `DATAMATIC_BLOCK` line, and only components/attributes with the flag set to the given value are looped over. In this case, the `HealthComponent` would be skipped over.

## Custom Extensions
By default, datamatic's runtime is quite basic, and you will most likely find yourself needing to extend it with code that is meaningful only for your codebase. For instance
* You may want your own custom types to be data members of your components
* You may require more complex code to be generated that cannot be expressed in datamatic's simplistic syntax

Datamatic exposes some hooks that allows you to enhance it with your own python code. Simply have files in your directory with the suffix `*.dmx.py`, and when datamatic scans your directory for template files, any `dmx` files will be discovered and imported. The hooks that you have access to here are described below.

## Types
One important thing needed for an effective code generator is the ability to convert a representation of an object from one form into another. In datamatic, this conversion is mainly from python/json to C++, with the prime example being the `default` attribute in the spec file being a json object that needs to be represented in C++. Datamatic uses the function `Types.parse(typename: str, json_object) -> str` for carrying out these conversions.

By default, the function is only defined when `typename` is either `"int"`, `"float"`, `"double"`, `"bool"` or `"std::string"`. Any other type results in a `RuntimeError`. However, this function can be extended by registering other types (notice in the above example the `TransformComponent` uses glm maths types). This is inspired by the `@functools.singledispatch` decorator in the standard library. Single dispatch is a form of polymorphism usually implemented based on the type of the first argument, however here we are dispatching based on the *value* of the first argument.

`parse` can be extended by using the `parse.register` decoratore. These extensions are done via a `dmx` file.

An example of a `dmx` file that extends `Types.parse` for `glm::vec3`:
```py
from Datamatic.Types import parse

@parse.register("glm::vec3")
def _(typename, obj) -> str:
    # For this implementation, typename == "glm::vec3"
    assert isinstance(obj, list)
    assert len(obj) == 3
    rep = ", ".join(parse("float", val) for val in obj)
    return f"{typename}{{{rep}}}"
```
With this in your codebase, `Types.parse("glm::vec3", obj)` would now be valid, only failing if the json object is not the correct form. Without this, the failure would be a `RuntimeError` saying that there was no parser for the specified type.

### Registering the same parser for different types
Consider the implementations of `glm::vec4` and `glm::quat`. They are both essentially a vector of four elements, so they can both use the same parser:
```py
from Datamatic.Types import parse

@parse.register("glm::vec4")
@parse.register("glm::quat")
def _(typename, obj) -> str:
    assert isinstance(obj, list)
    assert len(obj) == 4
    rep = ", ".join(parse("float", val) for val in obj)
    return f"{typename}{{{rep}}}"
```

### Parametrising parser functions
If you look at the above example, the implementation is the exact same as for `glm::vec3` except for the length check. It is also possible to have extra arguments to the parser to parametrise these. The values can then be passed in via the decorator. Thus it is possible to have all three of the above types use the same parser, along with `glm::vec2`:
```py
from Datamatic.Types import parse

@parse.register("glm::vec2", length=2)
@parse.register("glm::vec3", length=3)
@parse.register("glm::vec4", length=4)
@parse.register("glm::quat", length=4)
def _(typename, obj, length) -> str:
    assert isinstance(obj, list)
    assert len(obj) == length
    rep = ", ".join(parse("float", val) for val in obj)
    return f"{typename}{{{rep}}}"
```

These extra parameters can also have default values which will be used if they are not specified in the decorator:
```py
@parse.register("glm::vec2", length=2)
@parse.register("glm::vec3", length=3)
@parse.register("glm::vec4")
@parse.register("glm::quat")
def _(typename, obj, length=4) -> str: ...
```

## Plugins
As the syntax for datamatic is very simple, you may want to be able to express more complex things that simply the attributes in the spec file. For this, datamatic exposes a `Plugin` base class which can be subclassed in `dmx` files which allows the user to create functions in python that return strings that can be used in the templates. For example, you may want to generate C++ functions which print the component names in upper case. For this, you could create the following `dmx` file:
```py
from Datamatic.Plugins import Plugin

class Upper(Plugin):
    @compmethod
    def upper_name(cls, comp):
        return comp["name"].upper()
```
There are a few important things here:
* The class must derive from `Plugin`.
* For functions to be exposed to the template generator, they must be decorated with either `compmethod` or `attrmethod`, which act like `classmethod`, hence `cls` being the first argument. `@compmethod` adds the function to the `Comp` namespace and `@attrmethod` exposes the function to the `Attr` method. There is also `@compattrmethod` which adds it to both, but this not used often.

The above plugin can then be referenced in templates as `{{<namespace>.<plugin_name>.<function_name>}}`:
```cpp
#ifdef DATAMATIC_BLOCK
std::string {{Comp.name}}_upper()
{
    return "{{Comp.Upper.upper_name}}";
}

#endif
```
This would generate
```cpp
std::string NameComponent_upper()
{
    return "NAMECOMPONENT";
}

std::string HealthComponent_upper()
{
    return "HEALTHCOMPONENT";
}

std::string TransformComponent_upper()
{
    return "TRANSFORMCOMPONENT";
}
```
### The `builtin` Plugin
When writing something like `{{Comp.name}}`, this is not actually doing a simple attribute lookup from the spec. Instead this resolves to `{{Comp.builtin.name}}` and in fact calls a function called `name` in a provided plugin called `builtin`. This implementation is what you might expect:
```py
class builtin(Plugin):
    @compattrmethod
    def name(cls, obj):
        return obj["name"]
```
Note this uses `@compattrmethod` because it can also be used to access the name of an attribute. This is done primarily for two reasons:
* It makes "Attribute access" and "Plugin function" all uniform, which simplifies the implementation.
* It allows datamatic to add more builtin functions in an entensible way.

The `builtin` plugin also has some extra functionality and can be found [here](Datamatic/Plugins.py).

### Plugin Function Arguments
It is also possible to pass arguments to plugin functions using a `|` pipe syntax. For example, suppose you want to create a list of component types that's comma separated. You need a comma after each component except for the last one. This can be done using the builtin `Comp.if_not_last` function:
```cpp
using ECS = TemplatedECS<
#ifdef DATAMATIC_BLOCK
    {{Comp.name}}{{Comp.if_not_last|,}}
#endif
>;
```
The `Comp.if_not_last` takes one argument, and if the component is not the last component in the spec, the function resolves to the argument, otherwise it resolves to an empty string. The above example would produce:
```cpp
using ECS = TemplatedECS<
    NameComponent,
    HealthComponent,
    TransformComponent
>;
```
To access these arguments in the plugin, the function must have an `args` parameter:
```py
# in class builtin(Plugin):
    @compmethod
    def if_not_last(cls, comp, args: list[str]): ...
```
If the function call in the template code provides arguments but the function implementation does not have an `args` parameter, an error is raised. Conversely if a function implementation has an `args` parameter but the call in the template does not provide any, an error is raised. It is up to the function implementation to verify that the arguments passed make sense.

### Plugin Spec Access
For some plugin functions, it is not enough to simply have the current component or attribute. Some function require the entire component spec. For example, `Comp.if_not_last` must know the entire spec in order to know if the current component is the last. Plugins functions can request the spec by having a `spec` parameter. Thus `Comp.if_not_last` could be fully implemented as
```py
# in class builtin(Plugin):
    @compmethod
    def if_not_last(cls, comp, args, spec):
        assert len(args) == 1
        return args[0] if comp != spec["components"][-1] else ""
```

### Custom Data
It is also sometimes useful to tag components and attributes with custom data to be used within plugins. For this, the spec schema allows for a `custom` field which is not checked. This can be used to have any kind of information that you want. As an example, suppose you are creating a level editor and want a GUI for entity modification creating with [ImGUI](https://github.com/ocornut/imgui). You could create a plugin that returns ImGUI function calls for attributes depending on their type to easily generate this entire interface. However, you notice that sometimes you use a `glm::vec3` for a position, and in other places you use it to describe an RGB colour value. In your interface, you want a slider for position and a colour wheel for a colour. You could use a custom attribute in your spec file for this:
```json
{
    "name": "LightComponent",
    "display_name": "Light",
    "attributes": [
        {
            "name": "position",
            "display_name": "Light Position",
            "type": "glm::vec3",
            "default": [0.0, 0.0, 0.0],
            "custom": {
                "is_colour": false,
                "drag_speed": 0.1
            }
        },
        {
            "name": "colour",
            "display_name": "Light Colour",
            "type": "glm::vec3",
            "default": [1.0, 1.0, 1.0],
            "custom": {
                "is_colour": true
            }
        }
    ]
}
```
Then in the plugin you could write
```py
class Imgui(Plugin):
    @attrmethod
    def interface_function(cls, attr):
        name = attr["name"]
        display_name = attr["display_name"]
        ...
        if attr["type"] == "glm::vec3":
            if attr["custom"]["is_colour"]:
                return f'ImGui::ColorEdit3("{display_name}", &component.{name})'
            else:
                drag_speed = attr["custom"]["drag_speed"]
                return f'ImGui::DragFloat3("{display_name}", &component.{name}, drag_speed)'
        ...
```
I've included drag speed here to emphasise that custom data can be any kind of JSON object so it is not the same as flags and both have different use cases.

With the ability to generate template code using the full power of python, it should be possible to generate any kind of code you want. If there are still limitations, let me know, I would love to extend datamatic further to make it more useful!

## Future
* Have a nicer syntax for plugin function parameters as the pipe is a bit ugly. The current setup also cannot allow for passing a pipe symbol as a parameter.
* Extend the builtin plugin to provide more useful functionality.
* Support for more C++ standard types.
* Support for more languages. Currently this is able to work for C++ and I am also using it to generate Lua code as it is mostly language agnostic, but there are some C++ specific things. These things include the `#ifdef DATAMATIC_BLOCK` and the `Type` API. The reason I can use this for Lua is because you don't explicitly mention types so the `Type` API isn't a problem, and I don't make use of intellisense for Lua so the invalid syntax doesn't produce errors.
* I've considered having inline python code in the templates akin to using `eval`, which is often seen as dangerous, but we are already executing arbitrary code via the `dmx` system, so maybe it's no worse. I'm also considering going the other way and removing the discovery system and making users have to specify the extension files on the command line instead, but I haven't reached a conclusion here.
* A unit testing suite and some integration tests that can be run to show off the generator.
