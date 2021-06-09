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

DATAMATIC_BEGIN
    "{{Comp::name}}"{{Comp::if_not_last(",")}}
DATAMATIC_END
DATAMATIC_END
};


}
