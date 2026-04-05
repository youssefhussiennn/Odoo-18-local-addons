# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    analytic_account_sale_flag = fields.Boolean(comput="_get_analytic_account_sales_team")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    @api.onchange('partner_id', 'date')
    def _get_analytic_account_sales_team(self):
        for rec in self:
            rec.analytic_account_id = False
            if rec.team_id:
                rec.analytic_account_id = rec.team_id.analytic_account_id
            elif rec.team_id:
                rec.analytic_account_id = rec.team_id.analytic_account_id
            else:
                rec.analytic_account_id = False

            rec.analytic_account_sale_flag = True
            
                
    