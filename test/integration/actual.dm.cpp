#pragma once
#include <string>
#include <vector>

namespace integration {

// Components
DATAMATIC_BEGIN
struct {{Comp::name}}
{
    {{Attr::type}} {{Attr::name}} = {{Attr::default}};
};

DATAMATIC_END

// Test Flags
std::vector<std::string> types_with_flag_a_true = {
DATAMATIC_BEGIN FLAG_A=true
    "{{Comp::name}}"{{Comp::if_not_last(,)}}
DATAMATIC_END
};

std::vector<std::string> types_with_flag_b_false = {
DATAMATIC_BEGIN FLAG_B=false
    "{{Comp::test.foo}}"{{Comp::if_not_last(,)}}
DATAMATIC_END
};


}
