/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { blockUI, unblockUI } from "@web/core/ui/block_ui";

registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === "xlsx") {
        blockUI();
        try {
            await download({
                url: "/report_excel",
                data: action.data,
            });
        } finally {
            unblockUI();
        }
    }
});
