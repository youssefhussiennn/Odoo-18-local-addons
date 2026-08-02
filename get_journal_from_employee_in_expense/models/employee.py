# models/hr_employee.py

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"
   # _inherit = "account.payment.method.line"

    

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string="Payment Method"
    )