from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_cost = fields.Float(string='Cost', digits='Product Price', readonly=True, store=True)
    subcontract_margin = fields.Float(string='Margin', compute='_compute_subcontract_margin', store=True)

    @api.depends('price_unit', 'purchase_cost')
    def _compute_subcontract_margin(self):
        for line in self:
            if line.purchase_cost:
                line.subcontract_margin = (line.price_unit - line.purchase_cost) * (line.product_uom_qty or 1)
            else:
                line.subcontract_margin = 0.0
