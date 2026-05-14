/** @odoo-module */

import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { patch } from "@web/core/utils/patch";

patch(AccountReportFilters.prototype, {
    getSalespersonMultiRecordSelectorProps() {
        return this.getMultiRecordSelectorProps('res.users', 'salesperson_ids');
    },
});
