# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRExpense(models.Model):
    _inherit = "hr.expense"


    @api.onchange('employee_id', 'date')
    def _get_analytic_account_sales_team(self):
        for rec in self:
            rec.analytic_account_id = False
            if rec.employee_id.analytic_account_id:
                rec.analytic_account_id = rec.employee_id.analytic_account_id
            elif rec.employee_id.department_id:
                rec.analytic_account_id = rec.employee_id.department_id.analytic_account_id
            
            else:
                rec.analytic_account_id = False

            
