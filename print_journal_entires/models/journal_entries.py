# -*- encoding: UTF-8 -*-
from odoo import api, models

class AccountMove(models.Model):
    _inherit = "account.move"

    def total_debit_credit(self):
        res = {}
        for move in self:
            dr_total = 0.0
            cr_total = 0.0
            for line in move.line_ids:
                dr_total += line.debit
                cr_total += line.credit
            res.update({
                'cr_total': round(cr_total, 2),
                'dr_total': round(dr_total, 2)
                })
        return res
