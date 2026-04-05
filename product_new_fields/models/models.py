# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    country_of_origin_new = fields.Char(string="Country of Origin")
    usage_rate = fields.Char(string="Usage rate")
    composition = fields.Char(string="Composition")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    country_of_origin_new = fields.Char(string="Country of Origin", related="product_id.country_of_origin_new")
    usage_rate = fields.Char(string="Usage rate", related="product_id.usage_rate")
    composition = fields.Char(string="Composition", related="product_id.composition")