# -*- coding: utf-8 -*-
from odoo import models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_rfq_send(self):
        res = super().action_rfq_send()

        for order in self:
            order._portal_ensure_token()

        return res