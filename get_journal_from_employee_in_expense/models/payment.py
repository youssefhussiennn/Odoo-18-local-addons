# models/account_payment.py

from odoo import models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange('user_id')
    def _get_payment_method_from_employee(self):
        for rec in self:
            rec.payment_method_line_id = False

            if rec.user_id and rec.user_id.employee_id:
                employee = rec.user_id.employee_id

                if employee.payment_method_line_id:
                    rec.payment_method_line_id = employee.payment_method_line_id