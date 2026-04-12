# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """Extends purchase.order.line to display product specification fields
    directly on each product line inside a Purchase RFQ or Purchase Order.
    """

    _inherit = 'purchase.order.line'


    po_sub_category_id = fields.Many2one(
        related='product_id.product_tmpl_id.x_studio_many2one_field_BoGZB',
        string='Product Sub-category',
        store=True,       # stored in DB → usable in filters and group-by
        readonly=True,    # never editable here; change it on the product form
        help="Product Sub-category pulled from the selected product's template "
             "(source: x_studio_many2one_field_BoGZB on product.template)."
    )

    po_suggested_additions = fields.Char(
        related='product_id.product_tmpl_id.x_studio_suggested_additions',
        string='Suggested Additions',
        store=True,
        readonly=True,
        help="Suggested Additions pulled from the product template "
             "(source: x_studio_suggested_additions on product.template)."
    )


    po_composition = fields.Char(
        related='product_id.product_tmpl_id.composition',
        string='Composition',
        store=True,
        readonly=True,
        help="Composition pulled from the product template "
             "(source: composition on product.template, "
             "added by the product_new_fields module)."
    )

    po_formulation = fields.Char(
        related='product_id.product_tmpl_id.x_studio_formulation',
        string='Formulation',
        store=True,
        readonly=True,
        help="Formulation pulled from the product template "
             "(source: x_studio_formulation on product.template)."
    )

    po_color = fields.Char(
        related='product_id.product_tmpl_id.x_studio_color',
        string='Color',
        store=True,
        readonly=True,
        help="Color pulled from the product template "
             "(source: x_studio_color on product.template)."
    )


    po_p_uom = fields.Selection(
        related='product_id.product_tmpl_id.x_studio_p_uom',
        string='P_UOM',
        store=True,
        readonly=True,
        help="Package Unit of Measure pulled from the product template "
             "(source: x_studio_p_uom on product.template). "
             "Values: كجم = Kilogram, لتر = Liter."
    )

    product_weight = fields.Float(
        related='product_id.weight',
        string='Unit Weight (kg)',
        store=True,
        readonly=True,
        help="Weight pulled from the Product Variant's standard weight field."
    )

    # The calculated field for Ton
    order_quantity = fields.Float(
        string='Total (Tons)', 
        compute='_compute_order_quantity_ton', 
        store=True,
        digits=(16, 3), # Precise to 3 decimals
        help="Calculation: (Product Qty * Product Weight) / 1000"
    )

    @api.depends('product_qty', 'product_weight')
    def _compute_order_quantity_ton(self):
        for record in self:
            if record.product_qty and record.product_weight:
                # Math: Qty * Weight in KG / 1000 = Tons
                record.order_quantity = (record.product_qty * record.product_weight) / 1000.0
            else:
                record.order_quantity = 0.0
