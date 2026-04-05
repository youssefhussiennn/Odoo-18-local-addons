# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    price_after_discount = fields.Float('Price After Discount', digits='Product Price', compute='_compute_unit_price_after_discount')



    @api.depends('price_unit','discount','quantity')
    def _compute_unit_price_after_discount(self):
        
        for line in self:
            line.price_after_discount =  line.quantity * (line.price_unit - (line.price_unit * (line.discount/100)))
            
