# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_outgoing_incoming_moves(self, strict=False):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        moves = self.move_ids.filtered(
            lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id
        )
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(
                lambda r: fields.Date.to_date(r.date) <= self._context['accrual_entry_date']
            )

        for move in moves:
            if move.location_dest_id.usage == "customer":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "customer" and move.to_refund:
                incoming_moves |= move
            elif move.location_dest_id.usage != "customer" and move.product_id.invoice_policy == 'delivery':
                incoming_moves |= move

        return outgoing_moves, incoming_moves
