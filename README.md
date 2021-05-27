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

## Types

The basic types that are currently supported by default are `int`, `float`, `bool`, `std::string` and `std::any`. Notice in the above example the `TransformComponent` uses glm maths types. It is possible to add custom definitions for types. This is done by `*.dmx.py` files. When datamatic recurses through your repository to scan for templates, it also scans for these `dmx` files. Any that are found are imported. Datamatic exposes a base class called `Type` that you can subclass to give your own type definitions. As an example, this example project may have a `glm.dmx.py` file containing:
```py
from Datamatic.Types import Type, Float

class Vec3(Type):

    def __init__(self, val: list[float]):
        assert isinstance(val, list)
        assert all([isinstance(x, float) for x in val])
        self.x, self.y = [Float(t) for t in val]

    def __repr__(self):
        return f"{self.typename()}{{{self.x}, {self.y}}}"

    @staticmethod
    def typename():
        return "glm::vec3"
```
The `__init__` receives the parsed json object in the `default` attribute of the component to verify that it can be parsed, the `__repr__` should return the way it should be formatting in C++, and the `typename` should be the name of the type in C++. This is used to lookup the types found in the spec file.

Notice that it uses `Float`, which is the builtin implementation for floats, so type definitions can refer to other types. (This API is a bit clunky and will be revisited).

## Plugins
As the syntax for datamatic is very simple, you may want to be able to express more complex things that simply the attributes in the spec file. For this, datamatic also exposes a `Plugin` base class which can be subclassed in the `.dmx.py` files too which allows the user to create functions in python that return strings that can be used in the templates. For example, you may want to generate C++ function which print the component names in upper case. For this, you could create the following
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

### Flags

This is currently heavily WIP, currently there are some hardcoded flags that can be specified when defining a block in a template: `SCRIPTABLE` and `SAVABLE`. These
are flags that may be set on components and/or attributes, and when these flags are set, only components/attributes with those flags will get code generated for them.
This is going to be generalised. Currently, extra flags can be defined by users but they can only be used within Plugins currently.

## Future
- Generalise the flags concept and remove hardcoded flags from the core library.
- Look into other language support. Currently only C++ is properly supported. I have used this to generate Lua code as well, but most of that is done with a Plugin,
  whereas I'd like Datamatic to be more language agnostic, considering the bulk of the language specific stuff lives in the template files themselves.
