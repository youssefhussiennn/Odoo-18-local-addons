from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    tick = fields.Boolean(string="Select Product", default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    purchase_ids = fields.One2many('purchase.order', 'sale_order_id', string='Purchase Orders')

    purchase_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_count')

    def _compute_purchase_count(self):
        for order in self:
            # print("self.id", order.id)
            purchase_count = self.env['purchase.order'].search_count([('sale_order_id', '=', order.id)])
            self.purchase_count = purchase_count

#view purchase order generated from sale order

    def action_view_purchase_orders(self):
        for order in self:
            print("self.id", order.id)

            return {
                'name': _("Purchase Orders"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'domain': [('sale_order_id', '=',order.id)],
                'target': 'current',
                'view_mode':'list,form',
            }


    def action_create_purchase_orders(self):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for order in self:
            vendors = {}
            for line in order.order_line:
                if line.tick and line.vendor_id and line.product_id:
                    vendor = line.vendor_id
                    if vendor not in vendors:
                        vendors[vendor] = []
                    vendors[vendor].append(line)
                elif line.tick:
                    raise ValidationError(
                        'Please select a vendor for the product "%s" in order %s' % (line.product_id.name, order.name))
                else:
                    pass
                    # raise ValidationError('Please select products to create purchase orders in order %s' % order.name)

            for vendor, lines in vendors.items():
                purchase_order = PurchaseOrder.create({
                    'partner_id': vendor.id,
                    'origin': order.name,
                    'sale_order_id': order.id,
                })
                print('purchase_order', purchase_order)
                print("sale_order_id", order.name)

                for line in lines:
                    PurchaseOrderLine.create({
                        'order_id': purchase_order.id,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'price_unit': line.product_id.standard_price,
                    })
                    print('PurchaseOrderLine', PurchaseOrderLine)

                purchase_order.button_confirm()

        return True
