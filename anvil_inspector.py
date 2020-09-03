from .definitions import cpp_float
from datetime import datetime
header = """
#include "Inspector.h"
#include "EditorLayer.h"
#include "ImGuiXtra.h"
#include "Maths.h"
#include "Components.h"
#include "DevUI.h"

#include <imgui.h>

namespace Sprocket {

void ShowInspector(EditorLayer& editor)
{
    Entity entity = editor.Selected();

    if (editor.Selected().Null()) {
        if (ImGui::Button("New Entity")) {
            auto e = editor.GetScene()->NewEntity();
            editor.SetSelected(e);
        }
        return;
    }

    static DevUI::GizmoCoords coords = DevUI::GizmoCoords::WORLD;
    static DevUI::GizmoMode mode = DevUI::GizmoMode::TRANSLATION;
"""
transform = """
    if (entity.Has<TransformComponent>()) {
        auto& c = entity.Get<TransformComponent>();
        if (ImGui::CollapsingHeader("Transform")) {
            ImGui::PushID(1000000);
            ImGui::DragFloat3("Position", &c.position.x, 0.1f);
            ImGuiXtra::Euler("Orientation", &c.orientation);
            ImGui::DragFloat3("Scale", &c.scale.x, 0.1f);
            ImGuiXtra::GuizmoSettings(mode, coords);
            if (ImGui::Button("Delete")) { entity.Remove<TransformComponent>(); }
            ImGui::PopID();
        }

        if (!editor.IsGameRunning()) {
            auto& camera = editor.GetEditorCamera();
            auto tr = Maths::Transform(c.position, c.orientation, c.scale);
            ImGuizmo::Manipulate(
                Maths::Cast(camera.View()),
                Maths::Cast(camera.Proj()),
                GetMode(mode),
                GetCoords(coords),
                Maths::Cast(tr)
            );
            Maths::Decompose(tr, &c.position, &c.orientation, &c.scale);
        }
    }
"""
middle = """ 
    ImGui::Separator();

    if (ImGui::BeginMenu("Add Component")) {
"""

footer = """
        ImGui::EndMenu();
    }
    ImGui::Separator();
    if (ImGui::Button("Duplicate")) {
        Entity copy = Loader::Copy(editor.GetScene(), entity);
        editor.SetSelected(copy);
    }
    if (ImGui::Button("Delete Entity")) {
        entity.Kill();
        editor.ClearSelected();
    }
}
    
}
"""

def write_gui_attribute(attr):
    name = attr["Name"]
    display = attr["DisplayName"]
    cpp_type = attr["Type"]
    cpp_subtype = attr.get("Subtype")
    limits = attr.get("Limits")

    if cpp_type == "std::string":
        if cpp_subtype == "File":
            filt = attr["Data"]
            return f'        ImGuiXtra::File("{display}", editor.GetWindow(), &c.{name}, "{filt}");\n'
        return f'        ImGuiXtra::TextModifiable(c.{name});\n'
    if cpp_type == "float":
        if limits is not None:
            a, b = limits
            return f'        ImGui::SliderFloat("{display}", &c.{name}, {cpp_float(a)}, {cpp_float(b)});\n'
        return f'        ImGui::DragFloat("{display}", &c.{name}, 0.1f);\n'
    if cpp_type == "Maths::vec2":
        return f'        ImGui::DragFloat2("{display}", &c.{name}.x, 0.1f);\n'
    if cpp_type == "Maths::vec3":
        if cpp_subtype == "Colour":
            return f'        ImGui::ColorPicker3("{display}", &c.{name}.r);\n'
        return f'        ImGui::DragFloat3("{display}", &c.{name}.x, 0.1f);\n'
    if cpp_type == "Maths::vec4":
        if cpp_subtype == "Colour":
            return f'        ImGui::ColorPicker4("{display}", &c.{name}.r);\n'
        return f'        ImGui::DragFloat4("{display}", &c.{name}.x, 0.1f);\n'
    if cpp_type == "Maths::quat":
        return f'        ImGuiXtra::Euler("{display}", &c.{name});\n'
    if cpp_type == "bool":
        return f'        ImGui::Checkbox("{display}", &c.{name});\n'
    
    # Things like vectors and matrices and queues will get ignored for now
    return ""

def write_gui_component(idx, component):
    name = component["Name"]
    if name == "TransformComponent":
        return transform
        # Hardcoded for now until we think of a better way to handle the gizmo

    display = component["DisplayName"]
    out = f'    if (entity.Has<{name}>() && ImGui::CollapsingHeader("{display}")) {{\n'
    out += f'        ImGui::PushID({idx});\n'
    out += f'        auto& c = entity.Get<{name}>();\n'
    for attr in component["Attributes"]:
        out += write_gui_attribute(attr)
    out += f'        if (ImGui::Button("Delete")) {{ entity.Remove<{name}>(); }}\n'
    out += f'        ImGui::PopID();\n'
    out += f'    }}\n'
    return out

def generate(spec, output):
    out = f"// GENERATED FILE @ {datetime.now()}\n"
    out += header
    for idx, component in enumerate(spec["Components"]):
        out += write_gui_component(idx, component)
    out += middle
    for component in spec["Components"]:
        name = component["Name"]
        display = component["DisplayName"]
        out += f'        if (!entity.Has<{name}>() && ImGui::MenuItem("{display}")) {{\n'
        out += f'            {name} c;\n'
        out += f'            entity.Add(c);\n'
        out += f'        }}\n' 
    out += footer

    with open(output, "w") as outfile:
        outfile.write(out)