# Datamatic

A python package for generating C++ and Lua source code.

## Motivation

This is a tool designed to help with another project of mine where I am creating a game engine from scratch. That engine uses an ECS (Entity Component System), and
I kept finding areas where I needed to loop over all component types to implement logic, for example, exposing components to Lua, and displaying them withing an ImGui
editor window. This made adding new components very cumbersome.

With this tool, components can be defined in a json file, and C++ and Lua source templates can be provided which will be used to generate the actual files with the
components added in. I'm aware there existing tools out there for this job, but I thought it would be a fun exercise to implement my own.
