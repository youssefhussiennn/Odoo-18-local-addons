# -*- coding: utf-8 -*-

from pickle import TRUE
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    # team_id = fields.Many2one(related='move_id.team_id')
    analytic_account_flag = fields.Boolean(compute="_get_analytic_account_sales_team")

    # @api.depends('partner_id', 'date')
    # def _get_analytic_account_sales_team(self):
    #     for rec in self:
    #         rec.analytic_account_id = False
    #         if rec.partner_id.team_id:
    #             rec.analytic_account_id = rec.partner_id.team_id.analytic_account_id
    #         # elif rec.team_id:
    #         #     rec.analytic_account_id = rec.team_id.analytic_account_id
    #         else:
    #             rec.analytic_account_id = False
    #         rec.analytic_account_flag = True
                
    
    @api.depends('partner_id', 'date', 'invoice_line_ids', 'line_ids')
    def _get_analytic_account_sales_team(self):
        for this in self:
            this.analytic_account_flag = True
            for rec in this.invoice_line_ids:
                if rec.account_id.account_type in ['Income', 'الدخل', 'دخل آخر', 'Other Income', 'المصروفات', 'Expenses', 'إهلاك', 'Depreciation', 'تكاليف الدخل', 'Cost of Revenue']:
                    if rec.partner_id.team_id and this.move_type == 'entry':
                        rec.analytic_account_id = rec.partner_id.team_id.payment_analytic_account_id
                    elif rec.partner_id.team_id:
                        rec.analytic_account_id = rec.partner_id.team_id.analytic_account_id
