/** @odoo-module */

import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { patch } from "@web/core/utils/patch";

patch(AccountReportFilters.prototype, {
    getAnalyticTagMultiRecordSelectorProps() {
        return this.getMultiRecordSelectorProps('account.analytic.tag', 'analytic_tag_ids');
    },
});