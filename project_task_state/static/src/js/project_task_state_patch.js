/** @odoo-module **/

import { registry } from "@web/core/registry";

const fieldRegistry = registry.category("fields");
const originalWidget = fieldRegistry.get("project_state_selection");

if (originalWidget && originalWidget.component) {
    console.log("✅ Found project_state_selection widget, patching...");

    class CustomTaskStateWidget extends originalWidget.component {
        setup() {
            super.setup();
            console.log("⚙️ Running setup() for:", this.props.name, "on model:", this.props.record?.model);

            if (this.props.name === "state" && this.props.record?.model === "project.task") {
                const extraStates = [
                    ["on_going", "On Going"],
                    ["submitted", "Submitted"],
                ];
                const existing = new Set(this.selection?.map((s) => s[0]));
                const merged = [
                    ...(this.selection || []),
                    ...extraStates.filter(([val]) => !existing.has(val)),
                ];
                this.selection = merged;
                this.render();
                console.log("🔥 Updated state selection:", this.selection);
            }
        }
    }

    fieldRegistry.add(
        "project_state_selection",
        {
            ...originalWidget,
            component: CustomTaskStateWidget,
        },
        { force: true }
    );

    console.log("✅ Patched project_state_selection widget loaded successfully.");
} else {
    console.warn("⚠️ Could not find widget project_state_selection in registry.");
}
