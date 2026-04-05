from odoo import models,fields

class AddColumnExtra(models.Model):
    _inherit = 'sale.order.line'

    extra_des = fields.Text('Extra Description')