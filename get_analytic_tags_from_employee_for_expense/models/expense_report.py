# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRExpense(models.Model):
    _inherit = "hr.expense"


    @api.onchange('employee_id', 'date')
    def _get_analytic_tag_from_employee(self):
        for rec in self:
            rec.analytic_tag_ids = False
            if rec.employee_id.analytic_tag_ids:
                rec.analytic_tag_ids = rec.employee_id.analytic_tag_ids
            
            else:
                rec.analytic_tag_ids = False

            
