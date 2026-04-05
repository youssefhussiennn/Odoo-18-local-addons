from odoo import models, fields
from odoo.tools.sql import SQL

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    bonus = fields.Char(string="Bonus %", store=True)
    bonus_amount = fields.Float(string="Bonus Amount", store=True)

    def _select(self):
        return SQL("""
            %s,
            line.bonus AS bonus,
            line.bonus_amount AS bonus_amount
        """, super()._select())

    def _group_by(self):
        return SQL("""
            %s,
            line.bonus,
            line.bonus_amount
        """, super()._group_by())
