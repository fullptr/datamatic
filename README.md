# Datamatic
A python package for generating source code for entity component systems. This is entirely language agnostic and can generate code for any language.

[![Build Status](https://travis-ci.com/MagicLemma/datamatic.svg?branch=main)](https://travis-ci.com/MagicLemma/datamatic)
[![codecov](https://codecov.io/gh/MagicLemma/datamatic/branch/main/graph/badge.svg?token=4BJRUHXX5H)](https://codecov.io/gh/MagicLemma/datamatic)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/MagicLemma/datamatic/blob/main/LICENSE)

## Motivation
As part of another project, I am using an [Entity Component System](https::github.com/MagicLemms/apecs). However, I kept finding areas where I needed to loop over all component types to implement logic, for example, exposing components to Lua, displaying them withing an ImGui editor window, and writing serialisation code. This made adding new components very cumbersome, as there would be several different areas of the code that would need updating.

With this tool, components can be defined in a json file, and source code templates can be provided which will be used to generate the actual files with the components added in. With this approach, adding a new component is trivial; I just add it to the json component spec and rerun the tool and all the source code will be generated.

## Usage
Firstly, you must create a component spec json file. In its simplest form, this is just a dict with a single `"components"` field, which is a list of your components. An object representing a component must contain an `"attributes"` field which is a list of the attributes for that component. Other than that, you are free to add any fields you like to both your components and attributes.

For example, if you want your components to have a `"name"`, and you attributes to have a `"name"`, `"type"` and `"default"` value, you could define a spec that looks something like this:
```json
{
    "components": [
        {
            "name": "NameComponent",
            "attributes": [
                {
                    "name": "name",
                    "type": "std::string",
                    "default": "\"Entity\""
                }
            ]
        },
        {
            "name": "HealthComponent",
            "attributes": [
                {
                    "name": "current_health",
                    "type": "float",
                    "default": "100.0f"
                },
                {
                    "name": "max_health",
                    "type": "float",
                    "default": "100.0f"
                }
            ]
        },
        {
            "name": "TransformComponent",
            "attributes": [
                {
                    "name": "position",
                    "type": "glm::vec3",
                    "default": "{0.0f, 0.0f, 0.0f}"
                },
                {
                    "name": "orientation",
                    "type": "glm::quat",
                    "default": "{0.0f, 0.0f, 0.0f, 1.0f}"
                },
                {
                    "name": "scale",
                    "type": "glm::vec3",
                    "default": "{1.0f, 1.0f, 1.0f}"
                }
            ]
        }
    ]
}
```
Next, create some template files. These can exist anywhere in your repository and must have a `.dm.*` suffix. When datamatic is ran, the generated file will be created in the same location without the `.dm`. For example, if you have `components.dm.h`, a `components.h` file will be created. An example of a template file is below, notice how we are referring to the fields we have in our spec file:
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
* Replacement tokens are of the form `{{Namespace::field}}`.
* As seen above, if you instead specify the name of a property, that is returned (provided there is no function with the same name). Specifically, if no function with the given name is found, a default function is returned which simply does a property lookup on the given component/attribute.
* Aside from the property lookup functions used above, there are some builtin functions to provide some basic functionality, and datamatic also provides a way for you to provide your own custom python functions that can return any kind of string you like (more on that below).
* The block is copied for each of the components in the spec, and functions in the `Comp` namespace are called with the current component implicitly passed in. The `Attr` namespace works differently. If a line has an `Attr` symbol, that line is duplicated for each attribute in the component, so it isn't necessary to specify a loop when specifying attributes.
* The only valid namespaces are `Comp` and `Attr`.
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
By default, when a block of template code is processed, all components are looped over, and when an `Attr` token is found, all attributes in the component are looped over too. This is good for most cases, but there may be situations where you only want to loop over a subset of components, or maybe a subset for attributes.

For example, you may want to generate serialsation code, but there may be certain components and attributes that you may not want to save. This can be achieved using flags. You define flags by adding a field called `"flag_defaults"` to your spec, which list out all of your flags names along with their default value. You can then set these on components and attributes by giving them a `"flags"` field.

In the example below, I have a `DebugComponent` which is meant to be used to store a note for debugging only, and should not be part of a saved world. To exclude this from my serialisation code, I have defied a `"SERIALISABLE"` flag with a default value of `true`, and I have set the value of this flag on the entire `DebugComponent` to `false`. Further, I have added a new attribute to `HealthComponent` which will keep track of how long the entity has been alive for in this session. As I want this to reset if I reload the world, I don't want this attribute to be saved, so I have given it the same flag override.
```json
{
    "flag_defaults": {
        "SERIALISABLE": true
    },
    "components": [
        {
            "name": "DebugComponent",
            "flags": {
                "SERIALISABLE": false
            },
            "attributes": [
                {
                    "name": "note",
                    "type": "std::string",
                    "default: "\"\""
                }
            ]
        },
        {
            "name": "HealthComponent",
            "attributes": [
                {
                    "name": "current_health",
                    "type": "float",
                    "default": "100.0f"
                },
                {
                    "name": "max_health",
                    "type": "float",
                    "default": "100.0f"
                },
                {
                    "name": "time_alive_this_session",
                    "type": "double",
                    "default": "0.0",
                    "flags": {
                        "SERIALISABLE": false
                    }
                }
            ]
        }
    ]
}
```
Then the serialisation code template may look like
```cpp
DATAMATIC_BEGIN SERIALISABLE=true
    // Serialisation code here
DATAMATIC_END
```
Flags are passed on the `DATAMATIC_BEGIN` line, and only components/attributes with the flag set to the given value are looped over. In this case, the `DebugComponent` would be skipped over completely, and when generating code for the `HealthComponent`, any `Attr` line would skip the `time_alive_this_session` field.

## Functions
We previously mentioned that replacement tokens are of the form `{{Namespace::field}}`. This is not quite true; if it were, datamatic would be very restrictive with what you could express. If, for example, you needed the component name in capitals, the only way you could do that would be to add an extra field to your component spec and manually fill it in, which would be tedious and also error prone. To solve this, datamatic also can handle tokens of the form `{{Namespace::function(args)}}`, where the function is a function in python that receives the current spec, current component/attribute, and the specified `args`, and can return any string which is used in the output.

In fact, field lookup that we have seen so far is just a special case of this. What actually happens when datamatic encouters `{{Namespace::field}}` is:
* Look for a function called `field` in the "method register" (more on that soon).
* If a function is found, call that function. The return value is used in the generated file in place of the token.
* If a function is not found, return a "default" function that simply does a field lookup on the current component/attribute that we are generating code for.
* If there is no such field, an error is raied.

What functions are available? By default there are some very basic functions "builtin", but the real power here comes from letting users define and register their own custom methods written in python. To do this, simply have files in your directory with the suffix `*.dmx.py`, and when datamatic scans your directory for template files, any `dmx` files will be discovered and imported. These files should contain a `main` function that accepts one argument; this will be called with a `MethodRegister` object passed in. You can register your own functions with this to make them availble in templates. All `dmx` files will be imported before and code generation happens.

Going back to a previous example, suppose you want to generate C++ functions which print the component names in upper case. For this, you could create the following `dmx` file:
```py
def main(reg: method_register.MethodRegister):

    @reg.compmethod
    def format_upper(ctx):
        """
        Returns the current components name in upper case.
        """
        return ctx.comp["name"].upper()
```
There are a few important things here:
* The decorator `compmethod` adds the function to the `Comp` namespace, while `attrmethod` would add the function to the `Attr` namespace. A function can be added to both namespaces.
* The function name is important; it is what is used when referencing the function in template files.
* The `ctx` is a `Context` object containing the following fields:
    * `spec`: This is a modified copy of the json spec; the flags on the datamatic block are applied and any components/attributes that don't satify the flags are missing here. All flag data is also removed. Since `flag_defaults` is also omitted, the spec at this point is just a list of components, so they don't need to be accessed via `spec['components']`. If there are no flags set on a block (which is probably the most common), then the spec is still "filtered", but no components or attributes will be removed, only the flag data will vanish. Most custom functions will not need this, but it is here in case your custom function needs to know the position of the current components in the spec (as is the case with the builtin functions `if_not_last` and related).
    * `comp`: The current component that we are generating code for.
    * `attr`: The current attribute that we are generating code for. If the current function is a `compmethod`, then this field will be set to `None`.
    * `namespace`: This is a property, and is set to `"Attr"` if the `attr` field is not `None` and `"Comp"` othewise.


The above function can then be referenced in templates (note that if the function takes no arguments then the parentheses can be omitted):
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

### Function Arguments
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
    @reg.compmethod
    def if_not_last(ctx, arg):
```
Notice that if the template calls the function with an incorrect number of arguments, an exception will be raised when trying to call this function.

Another thing to note is that the parameter parsing is done by passing the contents in the parentheses to `ast.literal_eval`, so the parameters can be any of pythons primitive types, including lists, sets and dictionaries. However, note that if you use a set or dictionary, the curly braces could interfere with the parsing. For example, `{{Comp::if_not_last({1: "a": 2: {"b", "c"}})}}` could cause issues as the token would be parsed as `Comp::if_not_last({1: "a": 2: {"b", "c"`. Of course using anything other than a string for this function is probably unintended, but this is something users should be aware of when defining their own functions.

### Function-Only Data
As previously seen, fields on your components/attributes can be whatever you wish. However, if you are referencing these fields directly in your template files, they must be specified on all components/attributes.

A useful trick when writing custom functions is that you could provide fields that you will never reference in templates directly, and are there for custom functions only. In this case, those fields do not necessarily need to be on all components (provided your custom functions don't assume this), and they also don't need to be strings; you can attach arbitrary JSON objects in your spec to make use of these in your custom functions.

A example of this that I found useful was when generating code for a level editor. I had used datamatic to generate an [ImGUI](https://github.com/ocornut/imgui) UI for each component. This worked by writing a custom function in python that returned a string representing an ImGui function, with the specific function depending on the type of the attribute. This worked, however in some cases a `glm::vec3` (3D vector) represented a position, whereas in other cases it represented a colour. In both cases my UI was using a slider, however for the colours it would have been nicer to have a colour wheel. So I simply added `"is_colour": true` to all colour attributes. Further, for sliders, ImGUI lets you specify the drag speed, and since some attributes could be operating at differnt orders of magnitude, I wanted to be able to override this in my spec. So I also set a `"drag_speed"` field on some of my attributes, and used a defualt value for the rest. In my custom function I made use of these like so:
```py
@reg.attrmethod
def interface_component(ctx):
    attr = ctx.attr
    name = attr["name"]
    display_name = attr["display_name"] # This spec uses "display_name" as a field.
    ...
    if attr["type"] == "glm::vec3":
        if attr.get("is_colour"):
            return f'ImGui::ColorEdit3("{display_name}", &component.{name})'
        drag_speed = attr.get("drag_speed", 0.1) # Gets the value if it exists, defaulting to 0.1
        return f'ImGui::DragFloat3("{display_name}", &component.{name}, {drag_speed})'   
    ...
```
This is a very simple example that just required a bool, but there could be other things

## Afterword
With the ability to add flags to restrict some of the generation, and the ability to add custom python functions, I believe it should be possible to generate any kind of code you want. My focus now is to look into adding more builtin functions, and to make datamatic feel more ergonomic. If I spot a "trick" that I keep having to use in places, I'll consider adding features to make those simpler to do. If anyone else spots any limitations or has suggestions for features, let me know, I would love to extend datamatic further to make it more useful!
