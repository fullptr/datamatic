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
* The block is copied for each of the components in the spec, and functions in the `Comp` namespace are called with the current component implicitly passed in. The `Attr` namespace works differently. If a line has an `Attr` symbol, that line is duplicated for each attribute in the component, so it isn't necessary to specify a loop when specifying attributes.
* The only valid namespaces are `Comp` and `Attr`.
* `name`, `display_name` and `default` are examples of builtin functions.
* `name` and `display_name` simply return the value found in the component spec. `default` is a bit more complex as it needs to parse the json object in the spec into a string of C++ code. More on this later.
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
DATAMATIC_BEGIN SERIALISABLE=true
    // Serialisation code here
DATAMATIC_END
```
Flags are passed on the `DATAMATIC_BLOCK` line, and only components/attributes with the flag set to the given value are looped over. In this case, the `HealthComponent` would be skipped over.

## Custom Extensions
By default, datamatic's runtime is quite basic, and you will most likely find yourself needing to extend it with code that is meaningful for your codebase. For instance
* You may want your own custom types to be data members of your components
* You may require more complex code to be generated that cannot be expressed in datamatic's simplistic syntax

Most of the "business logic" is stored in a `Context` object, which is made available to users. Simply have files in your directory with the suffix `*.dmx.py`, and when datamatic scans your directory for template files, any `dmx` files will be discovered and imported. These files should contain a `main` function that accepts one argument; this will be called with the context passed as that argument. The features of this object are described more below.

## Types
The default values in the component spec are stored as json objects themselves rather than as a simple string of C++ code. This is done so that datamatic can provide a level of type checking for the values. Datamatic has type checkers for most standard library types and primitive types. If you were to, say, try to have `null` or `5` be the default value for a `std::string`, datamatic would raise an exception. This makes datamatic code less error-prone, but has the tradeoff that it doesn't know how to handle custom types. To fix this, the `Context` object provides a method for registering your own custom types. This lets you define a parser function to convert a JSON representation of your type into a string of C++ code.

Datamatic uses the function `ctx.parse(typename: str, json_object) -> str` for carrying out these conversions, and can be enhanced with the `ctx.types` decorator.

An example of a `dmx` file that extends `ctx.parse` for `glm::vec3`:
```py
def main(ctx):

    @ctx.type("glm::vec3")
    def _(typename, obj) -> str:
        # For this implementation, typename == "glm::vec3"
        assert isinstance(obj, list)
        assert len(obj) == 3
        rep = ", ".join(ctx.parse("float", val) for val in obj)
        return f"{typename}{{{rep}}}"
```
With this in your codebase, `ctx.parse("glm::vec3", obj)` would now be valid, only failing if the json object is not the correct form. Without this, the failure would be a `RuntimeError` saying that there was no parser for the specified type. Also note that this function delegates to the `float` parser for the vector elements.

### Registering the same parser for different types
Consider the implementations of `glm::vec4` and `glm::quat`. They are both essentially a vector of four elements, so they can both use the same parser:
```py
def main(ctx):

    @ctx.type("glm::vec4")
    @ctx.type("glm::quat")
    def _(typename, obj) -> str:
        assert isinstance(obj, list)
        assert len(obj) == 4
        rep = ", ".join(ctx.parse("float", val) for val in obj)
        return f"{typename}{{{rep}}}"
```

### Parametrised Parser Functions
If you look at the above example, the implementation is the exact same as for `glm::vec3` except for the length check. It is also possible to have extra arguments to the parser to parametrise these. The values can then be passed in via the decorator. Thus it is possible to have all three of the above types use the same parser, along with `glm::vec2`:
```py
def main(ctx):

    @ctx.type("glm::vec2", length=2)
    @ctx.type("glm::vec3", length=3)
    @ctx.type("glm::vec4", length=4)
    @ctx.type("glm::quat", length=4)
    def _(typename, obj, length) -> str:
        assert isinstance(obj, list)
        assert len(obj) == length
        rep = ", ".join(ctx.parse("float", val) for val in obj)
        return f"{`typename}{{{rep}}}"
```

These extra parameters can also have default values which will be used if they are not specified in the decorator:
```py
    @ctx.type("glm::vec2", length=2)
    @ctx.type("glm::vec3", length=3)
    @ctx.type("glm::vec4")
    @ctx.type("glm::quat")
    def _(typename, obj, length=4) -> str: ...
```

### Templated Parser Functions
So far we have just seen concrete type implementations. Datamatic also supports templated types. For example, the implementation of `std::vector<T>` is
```py
    @ctx.type("std::vector<{}>")
    def _(typename, subtype, obj) -> str:
        assert isinstance(obj, list)
        rep = ", ".join(ctx.parse(subtype, x) for x in obj)
        return f"{typename}{{{rep}}}"
```
This will match any type of the form `std::vector<{}>`, verifies the JSON object is a list, then verifies all of the subelements can be parsed as the matched subtype. Thus if you want a component to contain a vector of your custom type, you just need to provide the parser for the custom type.

You may have noticed that the signature of this parser is different. When a templated type is used, the subtypes that match with the brackets are passed into the parser as args in between `typename` and `obj`. If there were two sets of brackets, for example `std::map<{}, {}>`, then the parser function signature should be `(typename, keytype, valuetype, obj)`.

When calling `ctx.parse("std::vector<int>", [1, 2, 3])`, the following happens
* A concrete definition for `std::vector<int>` is looked up, which fails.
* The parser then loops through the templated functions until it finds one that matches. This uses [parse](https://pypi.org/project/parse/) under the hood.
* It matches `std::vector<int>` with `std::vector<{}>` and extracts the subtype as `int`.
* It calls the associated function with the arguments `("std::vector<int>", "int", [1, 2, 3])`.

### Example of a Templated Parametrized Parser Functions
Bringing it all together, the smart pointer parser is an example of a templated parametrized parser. It is templated because it contains a type, and it is parametrized because the default values rely on the `make_*` functions:
```py
    @ctx.type("std::unique_ptr<{}>", make_fn="std::make_unique")
    @ctx.type("std::shared_ptr<{}>", make_fn="std::make_shared")
    def _(typename, subtype, obj, make_fn) -> str:
        if obj is not None:
            return f"{make_fn}<{subtype}>{{{ctx.parse(subtype, obj)}}}"
        return "nullptr"
```

### Variadic Templatized Parser Functions
Even with all of this, we still cannot represent `std::tuple<Ts...>`, `std::variant<Ts...>`, or any type with a variadic number of types. This can be done using a variadic template parser function,:
```py
    @ctx.type("std::tuple<{}...>")
    def _(typename, subtypes, obj) -> str:  # Here, "subtypes" is a list of types
        assert isinstance(obj, list)
        assert len(subtypes) == len(obj)
        rep = ", ".join(ctx.parse(subtype, val) for subtype, val in zip(subtypes, obj))
        return f"{typename}{{{rep}}}"
```
It is not permitted to have a variadic template and a non-variadic template in the same parser, so something like `my_type<{}, {}...>` is not allowed. However, this can be implemented in the future. The way this works is by first removing the "..." from the string; that is only used to tell the parser to store this separately. After that, it then parses the captured string into the list of types. This is done character by character and counts the brackets ("(", "[", "<", "{"); only ending a current type if the brackets are balanced. This ensures that `"int, float, std::map<int, float>"` is parsed correctly and *not* parsed as `["int", "float", "std::map<int", "float>"]`.

### Standard Library Support
Most of the standard template library is implemented by default. Datamatic currently supports the following out of the box:
```cpp
std::vector<{}>
std::deque<{}>
std::queue<{}>
std::stack<{}>
std::list<{}>
std::forward_list<{}>

std::set<{}>
std::unordered_set<{}>
std::multiset<{}>
std::unordered_multiset<{}>

std::array<{}, {}>
std::pair<{}, {}>

std::map<{}, {}>
std::unordered_map<{}, {}>
std::multimap<{}, {}>
std::unordered_multimap<{}, {}>

std::optional<{}>
std::unique_ptr<{}>
std::shared_ptr<{}>
std::weak_ptr<{}>

std::tuple<{}...>
std::variant<{}...>
std::monostate

// No type checking done, default value is just a string that is substitued in unchecked
// Due to no type checking, the signature can be anything, so variadic templates are not needed
std::function<{}({})>
```

## Custom Functions
As we have already seen, functions can be called in template files with the syntax `{{Comp::name}}` for example. This is calling the function `name` which resides in the `Comp` namespace, and all it does it return the component name. There may be other things you wish to print that are more complicated that simply the properties of components and attributes. Via the `Context` object, you can also register your own functions, meaning you can format C++ strings using all the tools in python.

For a very simple example, suppose you want to generate C++ functions which print the component names in upper case. For this, you could create the following `dmx` file:
```py
def main(ctx):

    @ctx.compmethod("format.upper")
    def _(comp):
        return comp["name"].upper()
```
There are a few important things here:
* The decorator `compmethod` adds the function to the `Comp` namespace, while the `attrmethod` adds the function to the `Attr` namespace. A function can be added to both namespaces.
* The string in the decorator is the name of the function when exposed to template files. This is specified here rather than using the name of the function to allow punctuation in the funtion name. The convention here is to use periods to "namespace" the functions. This is purely for style; there is no notion of namespacing going on here. Builtin functions for attribute access is not namespaced, and there are some other builtin functions that are not namespaced described more below. To avoid name clashing, all user functions should be namespaced, as I may add more builtin functions to datamatic, which will not be namespaced.
* The `comp` parameter is the json object representing the component which comes directly from the json spec file.

The above function can then be referenced in templates:
```cpp
DATAMATIC_BEGIN
std::string {{Comp::name}}Upper()
{
    return "{{Comp::format.upper}}";
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
### Builtin Functions
As we have seen already, `{{Comp::name}}` calls the function `name` in the `Comp` namespace. This is an example of a builtin function. Builtin functions are exactly the same as custom functions, datamatic just explicitly calls `builtin.main(ctx)` before searching for user code, and it uses the exact same API. The implmentation is exactly what you might expect:
```py
def main(ctx):

    @ctx.compmethod("name")
    @ctx.attrmethod("name")
    def _(obj):
        return obj["name"]
```
You can find all of the builtin functions and type [here](datamatic/builtin.py).

### Plugin Function Arguments
We briefly mentioned earlier that replacement tokens can accept arguments. For example, suppose you want to create a list of component types that's comma separated. You need a comma after each component except for the last one. This can be done using the builtin `Comp::if_not_last` function:
```cpp
using ECS = TemplatedECS<
DATAMATIC_BEGIN
    {{Comp::name}}{{Comp::if_not_last(,)}}
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
    @ctx.compmethod("if_not_last")
    def _(comp, arg):
```
Notice that if the template calls the function with an incorrect number of arguments, an exception will be raised when trying to call this function.

### Plugin Spec Access
For some plugin functions, it is not enough to simply have the current component or attribute. Some function require the entire component spec. For example, `Comp::if_not_last` must know the entire spec in order to know if the current component is the last. The spec can be accessed through the `Context` object as `ctx.spec`. Thus `Comp::if_not_last` could be fully implemented as
```py
    @ctx.compmethod("if_not_last")
    def _(comp, arg):
        return arg if comp != ctx.spec["components"][-1] else ""
```
This does mean that custom functions could modify the spec, but obviously this is bad practice and you shouldn't do it.

### Custom Data
It is also sometimes useful to tag components and attributes with custom data to be used within plugins. For this, the spec schema allows for a `custom` field which is not checked. This can be used to have any kind of information that you want. As an example, suppose you are creating a level editor and want a GUI for entity modification created with [ImGUI](https://github.com/ocornut/imgui). You could create a custom function that returns ImGUI function call strings for attributes depending on their type to easily generate this entire interface. However, you notice that sometimes you use a `glm::vec3` for a position, and in other places you use it to describe an RGB colour value. In your interface, you want a slider for position and a colour wheel for a colour. You could use a custom attribute in your spec file for this:
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
Then in the function you could write
```py
    @ctx.attrmethod("interface.component")
    def _(attr):
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
* Have a nicer syntax for plugin function parameters. I would like to make the arguments comma separated and allow "," to be an argument as well. For this I will add a more sophisticated parser, but I haven't done it yet. After doing this, `Comp::if_not_last(,)` would become `Comp::if_not_last(",")` which is more akin to what people should expect.
* Extend the builtin plugin to provide more useful functionality.
* Support for more C++ standard types.
* Support for more languages. Currently this is able to work for C++ and I am also using it to generate Lua code as it is mostly language agnostic. The exception is the type parser code. I have some ideas for this but just haven't gotten around to doing it yet.
* I've considered having inline python code in the templates akin to using `eval`, which is often seen as dangerous, but we are already executing arbitrary code via the `dmx` system, so maybe it's no worse. I'm also considering going the other way and removing the discovery system and making users have to specify the extension files on the command line instead, but I haven't reached a conclusion here.
* A unit testing suite and some integration tests that can be run to show off the generator.

## Known Issues
* Flags and specwide functions don't play well together. For example, if I want to have a list of all types that satisfy certain flags, unless that set of types includes the last type, then the list will still have a comma at the end, even if using `{{Comp::if_not_last(,)}}`. These functions should only check the flagged components rather than the entire spec.
* The above issue highlights that custom functions do not have access to the flags set on the datamatic block. This is arguably a good thing, as the flags are only used to filter which components and attributes apply, and functions should not have access to that. However, this abtraction is broken by giving custom functions access to the entire spec. What should probably happen instead is that the context should contain a "filtered spec", giving functions access only to the components that are available in the spec. This would make things like `Comp::if_not_last` work as intended. (With more thought, the function api absolutely not have access to flags, that it what custom data is for. Flags are for filtering template blocks only).
