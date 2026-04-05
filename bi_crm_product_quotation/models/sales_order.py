from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    person_in_charge = fields.Many2one(
        'res.users', string='Person In Charge', default=lambda self: self.env.user)