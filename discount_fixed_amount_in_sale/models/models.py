# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discount = fields.Float(string='Discount (%)', digits=(16,6), default=0.0)
    discount_fixed_amount = fields.Float(string="Dis Fixed Amount", digits=(16,6))

    @api.onchange('price_unit', 'discount_fixed_amount', 'product_uom_qty')
    def auto_discount(self):

        

        if self.discount_fixed_amount and self.discount_fixed_amount != 0.0 and self.price_unit != 0.0:
            self.discount = (self.discount_fixed_amount/self.price_unit)*100
            # return
