# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_id = fields.Many2one('sale.commission',string="Sale Commission")
    commission_percntage = fields.Float(string="Percentage")
    commission_state = fields.Selection(
            string='Commission State',
            selection=[('paid', 'Paid'), ('not_paid', 'Not Paid')], 
            default='not_paid'
            
        )

    def action_update_commission_state(self):
        for rec in self:
            rec.write({'commission_state':'paid'})
    

