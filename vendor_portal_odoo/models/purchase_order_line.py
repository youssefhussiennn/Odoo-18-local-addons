# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # -------------------------
    # Related Fields from Product
    # -------------------------

    product_weight = fields.Float(
        related='product_id.weight',
        store=True,
        readonly=True
    )

    order_quantity_ton = fields.Float(
        compute='_compute_order_quantity_ton',
        store=True
    )
    product_sub_category_id = fields.Many2one(
        related='product_id.product_tmpl_id.x_studio_many2one_field_BoGZB',
        string='Product Sub-category',
        store=True,
        readonly=True,
        help="Product Sub-category taken from the selected product template"
    )

    product_suggested_additions = fields.Char(
        related='product_id.product_tmpl_id.x_studio_suggested_additions',
        string='Suggested Additions',
        store=True,
        readonly=True,
        help="Suggested Additions taken from the selected product template"
    )

    product_composition = fields.Char(
        related='product_id.product_tmpl_id.composition',
        string='Composition',
        store=True,
        readonly=True,
        help="Composition taken from the selected product template"
    )

    product_formulation = fields.Char(
        related='product_id.product_tmpl_id.x_studio_formulation',
        string='Formulation',
        store=True,
        readonly=True,
        help="Formulation taken from the selected product template"
    )

    product_color = fields.Char(
        related='product_id.product_tmpl_id.x_studio_color',
        string='Color',
        store=True,
        readonly=True,
        help="Color taken from the selected product template"
    )


    product_p_uom = fields.Selection(
        related='product_id.product_tmpl_id.x_studio_p_uom',
        string='P_UOM',
        store=True,
        readonly=True,
        help="Package Unit of Measure taken from the selected product template "
             "(Kilogram,Liter)"
    )


    @api.depends('product_qty', 'product_weight')
    def _compute_order_quantity_ton(self):
        for line in self:
            if line.product_qty and line.product_weight:
                line.order_quantity_ton = (line.product_qty * line.product_weight) / 1000.0
            else:
                line.order_quantity_ton = 0.0