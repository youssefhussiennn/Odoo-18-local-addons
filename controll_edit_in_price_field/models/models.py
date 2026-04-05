# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit="sale.order.line"

    price_flag = fields.Boolean(default=False, compute='_compute_partner_filter')

    @api.onchange('product_id')
    def _compute_partner_filter(self):
        for rec in self:
            price_flag = self.env['res.users'].has_group('account.group_account_manager')
            price_flag1 = self.env['res.users'].has_group('account.group_account_invoice')
            price_flag2 = self.env['res.users'].has_group('__export__.res_groups_142_26070ef8')
            if price_flag == True or price_flag1 == True or price_flag2 == True:
                rec.price_flag = True
            else:
                rec.price_flag = False


