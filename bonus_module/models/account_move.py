from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = "account.move"

    sales_bonus = fields.Many2one('sales.bonus', string="Sales Bonus")
