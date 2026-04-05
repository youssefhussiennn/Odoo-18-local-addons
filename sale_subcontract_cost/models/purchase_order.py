from odoo import models, api, _
import re

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _write_sale_purchase_cost(self):
        Sale = self.env['sale.order']
        for pol in self:

            origin = (pol.order_id.origin or '').strip()
            if not origin:
                continue

            # 🔥 Split origin by common separators (comma, slash, space)
            origin_list = [x.strip() for x in re.split('[,/ ]+', origin) if x.strip()]

            # 🔥 Find all matching SOs
            sale_orders = Sale.search([('name', 'in', origin_list)])
            if not sale_orders:
                continue

            # 🔥 Process each SO
            for so in sale_orders:
                candidates = so.order_line.filtered(lambda l: l.product_id == pol.product_id)

                if not candidates:
                    continue

                # Prefer lines with no purchase_cost first
                target_line = candidates.filtered(lambda l: not l.purchase_cost)
                target_line = target_line[0] if target_line else candidates[0]

                try:
                    target_line.sudo().write({'purchase_cost': pol.price_unit})
                except Exception:
                    pass

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.price_unit:
                rec._write_sale_purchase_cost()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'price_unit' in vals or 'order_id' in vals:
            for rec in self:
                if rec.order_id and rec.order_id.state in ('draft', 'sent', 'to approve', 'purchase'):
                    rec._write_sale_purchase_cost()
        return res
