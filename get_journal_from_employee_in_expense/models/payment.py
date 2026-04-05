# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"


    @api.onchange('user_id', 'date')
    def _get_journal_from_employee_od_user(self):
        for rec in self:
            # rec.journal_id = False
            if rec.user_id.employee_id and rec.user_id.employee_id.payment_journal_id:
                rec.journal_id = rec.user_id.employee_id.payment_journal_id
            # else:
            #     rec.journal_id = False

            
