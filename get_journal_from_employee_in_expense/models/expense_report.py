# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"


    @api.onchange('employee_id', 'date')
    def _get_journal_from_employee(self):
        for rec in self:
            rec.payment_method_line_id = False
            if rec.employee_id:
                rec.payment_method_line_id = rec.employee_id.journal_id
            else:
                rec.payment_method_line_id = False

            
