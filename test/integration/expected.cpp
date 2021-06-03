// GENERATED FILE
#pragma once
#include <string>
#include <vector>

namespace integration {

// Components
struct TemporaryComponent
{
};

struct NameComponent
{
    std::string name = "Entity";
};

struct PointComponent
{
    float x = 0.0f;
    float y = 0.0f;
};


// Test Flags
std::vector<std::string> types_with_flag_a_true = {
    "NameComponent",
    "PointComponent"
};


}
