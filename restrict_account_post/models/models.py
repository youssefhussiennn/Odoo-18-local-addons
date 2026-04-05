# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError




class AccountMove(models.Model):
    _inherit = 'account.move'
    def button_draft(self):
        # check if user in group "_import_.unpost"
        if self.env.user.has_group('__import__.unpost') or self.env.user.has_group('restrict_account_post.restrict_unpost'):
            return super(AccountMove, self).button_draft()
        else:
            raise UserError(_("غير مسموح بالتعديل يرجى مراجعه مدير النظام"))
    def _post(self, soft=True):
        # check if any account in move lines has res_group_id
        for line in self.line_ids:
            if line.account_id.res_group_id:
                # check if user has group
                if line.account_id.res_group_id.id not in self.env.user.groups_id.ids:
                    raise UserError(_("You don't have permission to post this account"))
        return super(AccountMove, self)._post(soft)
    
class AccountAccount(models.Model):
    _inherit = 'account.account'

    res_group_id = fields.Many2one('res.groups', string='Restrict Post Group')