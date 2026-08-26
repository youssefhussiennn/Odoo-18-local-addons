/** @odoo-module **/

/*
 * BEST-EFFORT / UNVERIFIED FILE
 * ------------------------------
 * I don't have the real source of account_reports' aged-partner-balance
 * frontend component, so the import path, class name, and the way options
 * get updated/reloaded below are educated guesses based on typical Odoo 18
 * OWL report-filter patterns, not a copy of the real file.
 *
 * If this throws in the browser console (F12) after installing/upgrading
 * the module, or the button just doesn't appear, paste me:
 *   1. The console error (if any)
 *   2. The real aged_partner_balance_filters.js /.xml content you find via
 *      the earlier find/Get-ChildItem command
 * and I'll fix this file exactly instead of guessing again.
 */

import { patch } from "@web/core/utils/patch";
import { AgedPartnerBalanceFilters } from "@account_reports/components/aged_partner_balance_filters/aged_partner_balance_filters";

patch(AgedPartnerBalanceFilters.prototype, {
    get customPeriodsEnabled() {
        return this.controller.options.custom_periods_enabled;
    },

    toggleCustomPeriods() {
        // Mirrors how the existing "Based on Due Date" / "30 Days" filters
        // in this same component are expected to trigger a report reload.
        this.controller.options.custom_periods_enabled = !this.controller.options.custom_periods_enabled;
        this.controller.reload();
    },
});
