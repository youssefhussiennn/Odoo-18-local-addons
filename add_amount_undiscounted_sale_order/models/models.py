# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)
    amount_discount = fields.Float('Discount Amount', compute='_compute_amount_undiscounted', digits=0)

    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            total_discount = 0.0
            for line in order.invoice_line_ids:
                total += line.price_subtotal + line.price_unit * ((line.discount or 0.0) / 100.0) * line.quantity  # why is there a discount in a field named amount_undiscounted ??
                total_discount += line.price_unit * ((line.discount or 0.0) / 100.0) * line.quantity  # why is there a discount in a field named amount_undiscounted ??
            order.amount_undiscounted = total
            order.amount_discount = total_discount

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_discount = fields.Float('Discount Amount', compute='_compute_amount_undiscounted', digits=0)

    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            total_discount = 0.0
            for line in order.order_line:
                total += line.price_subtotal + line.price_unit * ((line.discount or 0.0) / 100.0) * line.product_uom_qty  # why is there a discount in a field named amount_undiscounted ??
                total_discount += line.price_unit * ((line.discount or 0.0) / 100.0) * line.product_uom_qty  # why is there a discount in a field named amount_undiscounted ??
            order.amount_undiscounted = total
            order.amount_discount = total_discount
