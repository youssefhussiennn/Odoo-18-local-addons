from odoo import models, fields, api, _
from odoo.osv import expression


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'
    filter_ro_hide_account = True

    @api.model
    def _get_options_all_entries_domain(self, options):
        res = super(AccountReport, self)._get_options_all_entries_domain(options)
        if options.get('ro_hide_account'):
            res += [('account_id.hidden_report', '=', False)]
        print(res)
        return res
