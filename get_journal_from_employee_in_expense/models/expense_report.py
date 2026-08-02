# models/hr_expense_sheet.py

from odoo import models, api


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.onchange('employee_id')
    def _get_payment_method_from_employee(self):
        for rec in self:
            rec.payment_method_line_id = False

            if rec.employee_id and rec.employee_id.payment_method_line_id:
                rec.payment_method_line_id = rec.employee_id.payment_method_line_id.id