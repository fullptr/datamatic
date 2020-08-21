from datetime import datetime

header = """
#include "Serialiser.h"
#include "Log.h"
#include "Components.h"
#include "Maths.h"
#include "Yaml.h"

#include <yaml-cpp/yaml.h>
#include <fstream>

namespace Sprocket {

void Serialiser::Serialise(const std::string& file)
{
    YAML::Emitter out;
    out << YAML::BeginMap;
    out << YAML::Key << "Entities" << YAML::BeginSeq;
    d_scene->All([&](Entity& entity) {
        if (entity.Has<TemporaryComponent>()) { return; }

        out << YAML::BeginMap;
"""

middle = """
        out << YAML::EndMap;
    });
    out << YAML::EndSeq;
    out << YAML::EndMap;

    std::ofstream fout(file);
    fout << out.c_str();
}

void Serialiser::Deserialise(const std::string& file)
{
    d_scene->Clear();

    std::ifstream stream(file);
    std::stringstream sstream;
    sstream << stream.rdbuf();

    YAML::Node data = YAML::Load(sstream.str());
    if (!data["Entities"]) {
        return; // TODO: Error checking
    }

    auto entities = data["Entities"];
    for (auto entity : entities) {
        Entity e = d_scene->NewEntity();
"""

footer = """
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
            else:
                out += f'            c.{attr_name} = spec["{attr_name}"].as<{attr_type}>();\n'
    out += f'            e.Add(c);\n'
    out += "        }\n"
    return out

def generate(spec, output):
    out = f"// GENERATED FILE @ {datetime.now()}"
    out += header
    for component in spec["Components"]:
        out += write_serialiser(component, spec["Enums"])
    out += middle
    for component in spec["Components"]:
        out += write_deserialiser(component, spec["Enums"])
    out += footer
    
    with open(output, "w") as outfile:
        outfile.write(out)