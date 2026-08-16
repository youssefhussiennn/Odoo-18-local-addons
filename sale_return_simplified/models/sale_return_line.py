# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleReturnProductLine(models.Model):
    """Lines the user fills in — one row per product to return."""
    _name = 'sale.return.product.line'
    _description = 'Sale Return Product Line'

    return_id = fields.Many2one(
        'sale.return', required=True, ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])],
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit',
        compute='_compute_uom_id',
        store=True,
    )
    return_qty = fields.Float(
        string='Return Qty',
        required=True,
        digits='Product Unit of Measure',
        default=1.0,
    )

    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            line.uom_id = line.product_id.uom_id if line.product_id else False

    @api.constrains('return_qty')
    def _check_qty(self):
        for line in self:
            if line.return_qty <= 0:
                raise ValidationError(_('Return quantity must be greater than zero.'))


class SaleReturnInvoiceLine(models.Model):
    """Auto-generated after confirm — shows which invoices were used per product."""
    _name = 'sale.return.invoice.line'
    _description = 'Sale Return Invoice Breakdown'

    return_id = fields.Many2one(
        'sale.return', required=True, ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True,
    )
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', readonly=True,
    )
    invoice_date = fields.Date(
        string='Invoice Date', readonly=True,
    )
    return_qty = fields.Float(
        string='Returned Qty', readonly=True,
        digits='Product Unit of Measure',
    )
    price_unit = fields.Float(
        string='Unit Price', readonly=True,
        digits='Product Price',
    )
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        digits='Account',
    )
    credit_note_id = fields.Many2one(
        'account.move', string='Credit Note', readonly=True,
    )

    @api.depends('return_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.return_qty * line.price_unit
