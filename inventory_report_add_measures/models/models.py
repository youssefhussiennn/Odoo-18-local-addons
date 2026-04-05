# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

# class StockQuant(models.Model):
#     _inherit = 'stock.quant'
    
#     product_categ_id = fields.Many2one(related='product_id.categ_id', store=True, readonly=False)

#     @api.model
#     def _get_inventory_fields_create(self):
#         """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
#         """
#         res = super()._get_inventory_fields_create()
#         res += ['product_categ_id']
#         return res

#     @api.model
#     def _get_inventory_fields_write(self):
#         """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
#         """
#         res = super()._get_inventory_fields_write()
#         res += ['product_categ_id']
#         return res

class StockValuation(models.Model):
    _inherit = 'stock.valuation.layer'

    categ_id = fields.Many2one('product.category', related='product_id.categ_id', store=True)

