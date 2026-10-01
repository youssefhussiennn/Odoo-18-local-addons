/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

// Own report_type + registry key so report_xlsx's generic "xlsx" handler
// never sees this action (it would try to resolve the missing
// action.report_name as an XML ID).
registry
    .category("ir.actions.report handlers")
    .add("stock_location_xlsx", async (action, options, env) => {
        if (action.report_type !== "stock_location_xlsx") {
            return false;
        }
        // Odoo 17+/18: blocking the UI goes through the "ui" service,
        // there is no standalone blockUI() export anymore.
        env.services.ui.block();
        try {
            await download({
                url: "/report_excel",
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        return true;
    });
