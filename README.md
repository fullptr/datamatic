# Datamatic
A python package for generating C++ and Lua source code.

[![Build Status](https://travis-ci.com/MagicLemma/datamatic.svg?branch=main)](https://travis-ci.com/MagicLemma/datamatic)
[![codecov](https://codecov.io/gh/MagicLemma/datamatic/branch/main/graph/badge.svg?token=4BJRUHXX5H)](https://codecov.io/gh/MagicLemma/datamatic)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/MagicLemma/datamatic/blob/main/LICENSE)

## Motivation
As part of another project, I am using an [Entity Component System](https::github.com/MagicLemms/apecs). However, I kept finding areas where I needed to loop over all component types to implement logic, for example, exposing components to Lua, displaying them withing an ImGui editor window, and writing serialisation code. This made adding new components very cumbersome, as there would be several different areas of the code that would need updating.

With this tool, components can be defined in a json file, and C++ and Lua source templates can be provided which will be used to generate the actual files with the components added in. With this approach, adding a new component is trivial; I just add it to the json component spec and rerun the tool and all the source code will be generated.

## Usage
Firstly, you must create a component spec json file. As a basic example (flags, custom types and other features explained later):
```json
{
    "flag_defaults": [],
    "components": [
        {
            "name": "NameComponent",
            "display_name": "Name",
            "attributes": [
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "std::string",
                    "default": "\"Entity\""
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
                    "default": "100.0f"
                },
                {
                    "name": "max_health",
                    "display_name": "Maximum Health",
                    "type": "float",
                    "default": "100.0f"
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
                    "default": "{0.0f, 0.0f, 0.0f}"
                },
                {
                    "name": "orientation",
                    "display_name": "Orientation",
                    "type": "glm::quat",
                    "default": "{0.0f, 0.0f, 0.0f, 1.0f}"
                },
                {
                    "name": "scale",
                    "display_name": "Scale",
                    "type": "glm::vec3",
                    "default": "{1.0f, 1.0f, 1.0f}"
                }
            ]
        }
    ]
}
```
For a full description of what a valid schema is, see [Validator.py](Datamatic/Validator.py). Next, create some template files. These can exist anywhere in your repository and must have a `.dm.*` suffix. When datamatic is ran, the generated file will be created in the same location without the `.dm`. For example, if you have `components.dm.h`, a `components.h` file will be created. An example of a template file is:
```cpp
#include <glm/glm.hpp>

DATAMATIC_BEGIN
struct {{Comp::name}}
{
    {{Attr::type}} {{Attr::name}} = {{Attr::default}};
};

DATAMATIC_END
```
Notice a few things
* A block of template of code is defined by being between lines containing `DATAMATIC_BEGIN` and `DATAMATIC_END`.
* Replacement tokens are of the form `{{Namespace::function_name(args)}}`. If a function takes no arguments, the parentheses may be omitted. All of these functions return strings to insert into the output file.
* As seen above, if you instead specify the name of a property, that is returned (provided there is no function with the same name). Specifically, if no function with the given name is found, a default function is returned which simply does a property lookup on the given component/attribute.
* The block is copied for each of the components in the spec, and functions in the `Comp` namespace are called with the current component implicitly passed in. The `Attr` namespace works differently. If a line has an `Attr` symbol, that line is duplicated for each attribute in the component, so it isn't necessary to specify a loop when specifying attributes.
* The only valid namespaces are `Comp` and `Attr`.
* There is nothing special about `name`, `display_name` and `default` above, you can have any property on your components that you like. However, if you are making use of them directly like `{{Comp::name}}`, that property must obviously be provided for all components. It may be beneficial to have some properties that only appear on some components for the sake of custom functions, more on that below.
* A file can have multiple template blocks.

Running datamatic is very simple:
```bash
python datamatic.py --spec <path/to/json/spec> --dir <path/to/project/root>
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
You may have noticed in the spec file above that it contained a `flag_defaults` top level attribute. Flags provide a way to set boolean flags on components and attributes which can be used to ignore certain components/attributes in template blocks. For example, when saving a game, we may not want the health of entities to be saved (not a great example but it works to demonstrate the point). We can declare a flag called `SERIALISABLE` in the spec file in the following way
```json
{
    "flag_defaults": {
        "SERIALISABLE": true
    },
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
DATAMATIC_BEGIN SERIALISABLE=true
    // Serialisation code here
DATAMATIC_END
```
Flags are passed on the `DATAMATIC_BLOCK` line, and only components/attributes with the flag set to the given value are looped over. In this case, the `HealthComponent` would be skipped over.

## Functions (More Detail)
As mentioned earlier, replacement tokens in template files are of the form `{{Namespace::function_name(args)}}`, where the parentheses can be omitted if the function takes no arguements. By default, the only things available are some useful builtin functions as well as property lookup. As an example, suppose datamatic finds `{{Comp::name}}` when generating a file. The following happens:

* A function with the name `name` is looked up.
* If there is no such function, it returns the property `"name"` from the current component.
* If the current component has no `name` property, a `KeyError` will be raised and the generating will stop.

As the default offering is quite basic, you may find yourself needing to define your own functions in python that can generate more complex replacement strings. To do this, simply have files in your directory with the suffix `*.dmx.py`, and when datamatic scans your directory for template files, any `dmx` files will be discovered and imported. These files should contain a `main` function that accepts one argument; this will be called with a `MethodRegister` object passed in. You can register your own functions with this to make them availble in templates. All `dmx` files will be imported before and code generation happens.

For a very simple example, suppose you want to generate C++ functions which print the component names in upper case. For this, you could create the following `dmx` file:
```py
def main(reg: method_register.MethodRegister):

    @reg.compmethod
    def format_upper(ctx):
        return ctx.comp["name"].upper()
```
There are a few important things here:
* The decorator `compmethod` adds the function to the `Comp` namespace, while `attrmethod` would add the function to the `Attr` namespace. A function can be added to both namespaces.
* The function name is important; it is what is used when referencing the function in template files.
* The `ctx` is a `Context` object containing the following fields:
    * `spec`: This is a modified copy of the json spec; the flags on the datamatic block are applied and any components/attributes that don't satify the flags are filtered out here. All flag data is also removed. Since `flag_defaults` is also omitted, the spec at this point is just a list of components, so they don't need to be accessed via `spec['components']`. If there are no flags set on a block (which is probably the most common), then the spec is still "filtered", but no components or attributes will be removed, only the flag data will vanish.
    * `comp`: The current component that we are generating code for. This is provided as some functions may need to be aware of which position the current component is in (see `if_not_last`).
    * `attr`: The current attribute that we are generating code for. If the current function is a `compmethod`, then this field will be set to `None`.
    * `namespace`: This is a property, and is set to `"Attr"` if the `attr` field is not `None` and `"Comp"` othewise.


The above function can then be referenced in templates:
```cpp
DATAMATIC_BEGIN
std::string {{Comp::name}}Upper()
{
    return "{{Comp::format_upper}}";
}

DATAMATIC_END
```
This would generate
```cpp
std::string NameComponentUpper()
{
    return "NAMECOMPONENT";
}

std::string HealthComponentUpper()
{
    return "HEALTHCOMPONENT";
}

std::string TransformComponentUpper()
{
    return "TRANSFORMCOMPONENT";
}

```

### Custom Function Arguments
We briefly mentioned earlier that replacement tokens can accept arguments, so let's take a look at how this works and how custom functions can make use of this. For example, suppose you want to create a list of component types that's comma separated. You need a comma after each component except for the last one. This can be done using the builtin `Comp::if_not_last` function:
```cpp
using ECS = TemplatedECS<
DATAMATIC_BEGIN
    {{Comp::name}}{{Comp::if_not_last(",")}}
DATAMATIC_END
>;
```
The `Comp::if_not_last` takes one argument, and if the component is not the last component in the spec, the function resolves to the argument, otherwise it resolves to an empty string. The above example would produce:
```cpp
using ECS = TemplatedECS<
    NameComponent,
    HealthComponent,
    TransformComponent
>;
```
These arguments are then passed to the function definition in the order they appear:
```py
    @ctx.compmethod
    def if_not_last(ctx, arg):
```
Notice that if the template calls the function with an incorrect number of arguments, an exception will be raised when trying to call this function.

Another thing to note is that the parameter parsing is done by passing the contents in the parentheses to `ast.literal_eval`, so the parameters can be any of pythons primitive types, including lists, sets and dictionaries. However, note that if you use a set or dictionary, the curly braces could interfere with the parsing. For example, `{{Comp::if_not_last({1: "a": 2: {"b", "c"}})}}` could cause issues as the token would be parsed as `Comp::if_not_last({1: "a": 2: {"b", "c"`. Of course using anything other than a string for this function is probably unintended, but this is something users should be aware of when defining their own functions.

### Custom Data
As mentioned, the properties that you choose to have on your components/attributes can be anything you want. It may also be useful to have properties that don't exist on all components, which should not be access directly in template files by attribute lookup, but may be used in custom functions.

As an example, suppose you are creating a level editor and want a GUI for entity modification created with [ImGUI](https://github.com/ocornut/imgui). You could create a custom function that returns strings containing ImGUI function calls for attributes depending on their type to easily generate this entire interface. However, you notice that sometimes you use a `glm::vec3` for a position, and in other places you use it to describe an RGB colour value. In your interface, you want a slider for position and a colour wheel for a colour. You could use a custom attribute in your spec file for this:
```json
{
    "name": "LightComponent",
    "display_name": "Light",
    "attributes": [
        {
            "name": "position",
            "display_name": "Light Position",
            "type": "glm::vec3",
            "default": "{0.0f, 0.0f, 0.0f}",
            "is_colour": false,
            "drag_speed": 0.1,
        },
        {
            "name": "colour",
            "display_name": "Light Colour",
            "type": "glm::vec3",
            "default": "{1.0f, 1.0f, 1.0f}",
            "is_colour": true
        }
    ]
}
```
Then in the function you could write
```py
    @reg.attrmethod
    def interface_component(ctx):
        attr = ctx.attr
        name = attr["name"]
        display_name = attr["display_name"]
        ...
        if attr["type"] == "glm::vec3":
            if attr["custom"].get("is_colour", False):
                return f'ImGui::ColorEdit3("{display_name}", &component.{name})'
            else:
                drag_speed = attr["custom"]["drag_speed"]
                return f'ImGui::DragFloat3("{display_name}", &component.{name}, drag_speed)'
        ...
```
If a property is not intended to be called directly from templates, there is no need to restrict them to being strings (technically nothing is stopping you from using non-strings for accessable properties, but the generated code may be weird as the value will be stringified).

With the ability to generate template code using the full power of python, it should be possible to generate any kind of code you want. If there are still limitations, let me know, I would love to extend datamatic further to make it more useful!
