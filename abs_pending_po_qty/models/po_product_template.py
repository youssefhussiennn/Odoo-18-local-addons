# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2021-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _

class PurchaseOrderProductProduct(models.Model):
    _inherit = "product.product"

    purchase_order_qty = fields.Integer(string="Total Purchase Order", compute='_compute_pending_purchase_order_qty')

    def _compute_pending_purchase_order_qty(self):
        for product in self:
            if product.purchase_order_qty:
                continue
            if product:
                purchase_order_qty = 0
                purchase_order_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.id),
                    ('order_id.state', 'not in', ('cancel', 'sent', 'to approve')),
                    ('order_id.x_studio_type', '=', 'Global'),
                ])
                if purchase_order_line:
                    for pol in purchase_order_line:
                        weight = pol.x_studio_product_weight if pol.x_studio_product_weight != 0 else 1
                        remaining_units = pol.product_qty - pol.qty_received

                        if weight > 1:
                            product.purchase_order_qty += remaining_units / weight
                        else:
                            product.purchase_order_qty += remaining_units * weight
                                            
    def display_pending_purchase_order_qty(self):
        if self.id:
            template_id = self.env.ref('abs_pending_po_qty.purchase_order_line_tree_custom_view').id
            product_ids = []
            po_line = self.env['purchase.order.line'].search([
                ('product_id', '=', self.id),
                ('order_id.state', 'not in', ('cancel', 'sent', 'to approve')),
                ('order_id.x_studio_type', '=', 'Global'),
            ])
            for line_id in po_line:
                product_ids.append(line_id.id)
            return {
                'name': _('List of Pending purchase Order Lines'),
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'purchase.order.line',
                'type': 'ir.actions.act_window',
                'view_id': template_id,
                'views': [(self.env.ref('abs_pending_po_qty.purchase_order_line_tree_custom_view').id, 'tree')],
                'domain': [('id', 'in', product_ids)]
            }
