from datetime import datetime

from . import definitions

header = """
#include "Loader.h"
#include "Log.h"
#include "Components.h"
#include "Maths.h"
#include "Yaml.h"
#include "Scene.h"
#include "Updater.h"

#include <yaml-cpp/yaml.h>
#include <fstream>
#include <memory>

namespace Sprocket {
namespace Loader {

void Save(const std::string& file, std::shared_ptr<Scene> scene)
{
    YAML::Emitter out;
    out << YAML::BeginMap;
"""

middle0 = """
    out << YAML::Key << "Entities" << YAML::BeginSeq;
    scene->All([&](Entity& entity) {
        if (entity.Has<TemporaryComponent>()) { return; }

        out << YAML::BeginMap;
"""

middle1 = """
        out << YAML::EndMap;
    });
    out << YAML::EndSeq;
    out << YAML::EndMap;

    std::ofstream fout(file);
    fout << out.c_str();
}

void Load(const std::string& file, std::shared_ptr<Scene> scene)
{
    scene->Clear();

    std::ifstream stream(file);
    std::stringstream sstream;
    sstream << stream.rdbuf();

    YAML::Node data = YAML::Load(sstream.str());
    UpdateScene(data);
    if (!data["Entities"]) {
        return; // TODO: Error checking
    }

    auto entities = data["Entities"];
    for (auto entity : entities) {
        Entity e = scene->NewEntity();
"""

middle2 = """
    }
}

Entity Copy(std::shared_ptr<Scene> scene, Entity entity)
{
    Entity e = scene->NewEntity();
"""

footer = """
    return e;
}

void Copy(std::shared_ptr<Scene> source, std::shared_ptr<Scene> target)
{
    target->Clear();
    source->All([&](Entity& entity) {
        Copy(target, entity);
    });
}

}
}
"""

def write_serialiser(component, enums):
    name = component["Name"]
    attrs = component["Attributes"]
    out = f"        if(entity.Has<{name}>()) {{\n"
    out += f"            const auto& c = entity.Get<{name}>();\n"
    out += f'            out << YAML::Key << "{name}" << YAML::BeginMap;\n'
    for attr in attrs:
        attr_name = attr["Name"]
        if attr.get("Savable", True):
            if attr["Type"] in enums:
                out += f'            out << YAML::Key << "{attr_name}" << YAML::Value << static_cast<int>(c.{attr_name});\n'
            else:
                out += f'            out << YAML::Key << "{attr_name}" << YAML::Value << c.{attr_name};\n'
    out += "            out << YAML::EndMap;\n"
    out += "        }\n"
    return out

def write_deserialiser(component, enums):
    name = component["Name"]
    attrs = component["Attributes"]
    out = f'        if (auto spec = entity["{name}"]) {{\n'
    out += f'            {name} c;\n'
    for attr in attrs:
        attr_name = attr["Name"]
        attr_type = attr["Type"]
        if attr.get("Savable", True):
            if attr["Type"] in enums:
                out += f'            c.{attr_name} = static_cast<{attr_type}>(spec["{attr_name}"].as<int>());\n'
            elif "Default" in attr:
                out += f'            c.{attr_name} = spec["{attr_name}"] ? spec["{attr_name}"].as<{attr_type}>() : {definitions.default_cpp_repr(attr_type, attr["Default"])};\n'
            else:
                out += f'            c.{attr_name} = spec["{attr_name}"].as<{attr_type}>();\n'
    out += f'            e.Add(c);\n'
    out += "        }\n"
    return out

def write_copy(component):
    name = component["Name"]
    out = f"    if (entity.Has<{name}>()) {{\n"
    out += f"        e.Add<{name}>(entity.Get<{name}>());\n"
    out += "    }\n"
    return out

def generate(spec, output):
    version = spec.get("Version", 0)
    out = f"// GENERATED FILE @ {datetime.now()}"
    out += header
    out += f'    out << YAML::Key << "Version" << YAML::Value << {version};'
    out += middle0
    for component in spec["Components"]:
        out += write_serialiser(component, spec["Enums"])
    out += middle1
    for component in spec["Components"]:
        out += write_deserialiser(component, spec["Enums"])
    out += middle2
    for component in spec["Components"]:
        out += write_copy(component)
    out += footer
    
    with open(output, "w") as outfile:
        outfile.write(out)