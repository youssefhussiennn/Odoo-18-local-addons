# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sales_order = fields.Many2one('sale.order', string='Sales Order', copy=False)
    
class SalesOrder(models.Model):
    _inherit = 'sale.order'
    
    # advanced_payment_count = fields.Integer(compute='compute_count')
    expenses_count = fields.Integer(compute='compute_count_expenses')
    # payment_count = fields.Integer(compute='compute_count_payment')
    
    # def get_advanced_payment(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Advanced Payment',
    #         'view_mode': 'tree',
    #         'res_model': 'account.move.line',
    #         'domain': [('sales_order', '=', self.id),('account_id.account_type','=','asset_prepayments')],
    #         'context': "{'create': False}"
    #     }
        
    # def compute_count(self):
    #     for record in self:
    #         domain = [
    #             ('sales_order', '=', record.id),
    #             ('account_id.account_type', '=', 'asset_prepayments'),
    #             ('parent_state', '=', 'posted')
    #         ]
    #         record.advanced_payment_count = self.env['account.move.line'].search_count(domain)
            
    def get_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses',
            'view_mode': 'list',
            'res_model': 'account.move.line',
            'domain': [('sales_order', '=', self.id),('account_id.account_type','=','expense_direct_cost')],
            'context': "{'create': False}"
        }
        
    def compute_count_expenses(self):
        for record in self:
            domain = [
                ('sales_order', '=', record.id),
                ('account_id.account_type', '=', 'expense_direct_cost'),
                ('parent_state', '=', 'posted')
            ]
            record.expenses_count = self.env['account.move.line'].search_count(domain)
            
    # def get_payment(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Payment',
    #         'view_mode': 'tree',
    #         'res_model': 'account.move.line',
    #         'domain': [('sales_order', '=', self.id),('account_id.account_type','=','liability_payable')],
    #         'context': "{'create': False}"
    #     }
        
    # def compute_count_payment(self):
    #     for record in self:
    #         domain = [
    #             ('sales_order', '=', record.id),
    #             ('account_id.account_type', '=', 'liability_payable'),
    #             ('parent_state', '=', 'posted')
    #         ]
    #         record.payment_count = self.env['account.move.line'].search_count(domain)
