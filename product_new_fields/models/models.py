# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    country_of_origin_new = fields.Char(string="Country of Origin",tracking=True)
    usage_rate = fields.Char(string="Usage rate",tracking=True)
    composition = fields.Char(string="Composition",tracking=True)
    color = fields.Char(string="Color",tracking=True)
    pests = fields.Char(string="الأوبئة",tracking=True)
    crop = fields.Char(string="المحصول",tracking=True)
    formulation = fields.Char(string="Formulation",tracking=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    country_of_origin_new = fields.Char(string="Country of Origin", related="product_id.country_of_origin_new")
    usage_rate = fields.Char(string="Usage rate", related="product_id.usage_rate")
    composition = fields.Char(string="Composition", related="product_id.composition")
    color = fields.Char(string="Color",related="product_id.color")
    pests = fields.Char(string="الأوبئة",related="product_id.pests")
    crop = fields.Char(string="المحصول",related="product_id.crop")
    formulation = fields.Char(string="Formulation",related="product_id.formulation")