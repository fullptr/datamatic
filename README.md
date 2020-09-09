# Datamatic

A python package for generating C++ and Lua source code.

## Motivation

This is a tool designed to help with another project of mine where I am creating a game engine from scratch. That engine uses an ECS (Entity Component System), and
I kept finding areas where I needed to loop over all component types to implement logic, for example, exposing components to Lua, and displaying them withing an ImGui
editor window. This made adding new components very cumbersome.

With this tool, components can be defined in a json file, and C++ and Lua source templates can be provided which will be used to generate the actual files with the
components added in. I'm aware there existing tools out there for this job, but I thought it would be a fun exercise to implement my own.


## Usage

Running Datamatic is very simple. It has no external dependencies so can just be cloned and ran on a repository as follows:
```
python3.8 Datamatic.py --spec <path/to/json/spec> --dir <path/to/project>
```

Datamatic will then recurse through the entire directory looking for files with extensions `*.dm.*`, and use those as templates for generating source code, which it 
will place alongside the template files with the `.dm` removed. So far, it has been tested with `.dm.h`, `.dm.cpp` and `.dm.lua` files.

![Overview](res/Overview.png)

### Spec

This is currently changing a lot as Datamatic evolves, see [here](Datamatic/Validator.py) to see the current schema validator.

### Types

The basic types that are supported by default are int, float, bool and std::string. Users can define new types by subclassing CppType. These can be placed anywhere
inside the target repo within a `*.dmx.py` file and Datamatic will automatically discover it.

### Plugins

The syntax for Datamatic is very simple, and as such it may not be capable of generating the desired code. To this end, it is possible to create Plugins to allow
users to define text replacement functions using the full power of Python. These can be placed anywhere inside the target repo within a `*.dmx.py` file and
Datamatic will discover them.

![Plugins](res/Plugin.png)

### Flags

This is currently heavily WIP, currently there are some hardcoded flags that can be specified when defining a block in a template: `SCRIPTABLE` and `SAVABLE`. These
are flags that may be set on components and/or attributes, and when these flags are set, only components/attributes with those flags will get code generated for them.
This is going to be generalised. Currently, extra flags can be defined by users but they can only be used within Plugins currently.

## Future
- Generalise the flags concept and remove hardcoded flags from the core library.
- Remove the hardcoded `Maths::*` types. These are artifacts from my game engine project. It should be possible for users to define custom types. `int`, `float`, `bool`
  and `std::string` will be considered as "built in" types. These will either be specified within the spec file or be done in a similar way to Plugins as python files
  that get automatically discovered.
- Look into other language support. Currently only C++ is properly supported. I have used this to generate Lua code as well, but most of that is done with a Plugin,
  whereas I'd like Datamatic to be more language agnostic, considering the bulk of the language specific stuff lives in the template files themselves.
