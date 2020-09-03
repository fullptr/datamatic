#define TIME_STAMP
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
    out << YAML::Key << "Version" << YAML::Value << 2;
    const auto& sun = scene->GetSun();
    out << YAML::Key << "Sun" << YAML::BeginMap;
    out << YAML::Key << "direction" << YAML::Value << sun.direction;
    out << YAML::Key << "colour" << YAML::Value << sun.colour;
    out << YAML::Key << "brightness" << YAML::Value << sun.brightness;
    out << YAML::EndMap;

    out << YAML::Key << "Entities" << YAML::BeginSeq;
    scene->All([&](Entity& entity) {
        if (entity.Has<TemporaryComponent>()) { return; }
        out << YAML::BeginMap;
#define LOADER_SAVE_IMPL
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

    if (auto sun = data["Sun"]) {
        scene->GetSun().direction = sun["direction"] ? sun["direction"].as<Maths::vec3>() : Maths::vec3{0.0, -1.0, 0.0};
        scene->GetSun().colour = sun["colour"] ? sun["colour"].as<Maths::vec3>() : Maths::vec3{1.0, 1.0, 1.0};
        scene->GetSun().brightness = sun["brightness"] ? sun["brightness"].as<float>() : 1.0f;
    }

    if (!data["Entities"]) {
        return; // TODO: Error checking
    }

    auto entities = data["Entities"];
    for (auto entity : entities) {
        Entity e = scene->NewEntity();
#define LOADER_LOAD_IMPL
    }
}

Entity Copy(std::shared_ptr<Scene> scene, Entity entity)
{
    Entity e = scene->NewEntity();
#define LOADER_COPY_IMPL
    return e;
}

void Copy(std::shared_ptr<Scene> source, std::shared_ptr<Scene> target)
{
    target->Clear();
    target->GetSun() = source->GetSun();
    source->All([&](Entity& entity) {
        Copy(target, entity);
    });
}

}
}
