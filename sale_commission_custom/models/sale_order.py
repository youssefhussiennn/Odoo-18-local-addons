# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_id = fields.Many2one('sale.commission',string="Sale Commission")

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['commission_id'] = self.commission_id.id
        return res
