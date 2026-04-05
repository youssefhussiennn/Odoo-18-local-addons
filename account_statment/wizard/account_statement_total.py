# -*- coding: utf-8 -*-
import time
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountStatementTotalWizard(models.TransientModel):
    _name = 'account.statement.total.wizard'
    
    partner_id = fields.Many2one('res.partner', string="Partner", domain=['|',('customer_rank','>=',1),('supplier_rank','>=',1), '|', ('invoice_ids','!=', False), ('total_due', '!=', 0)])
    team_id = fields.Many2one('crm.team', string="Sales Team")
    user_ids = fields.Many2many('res.users', string='SalesPerson')
    allowed_members = fields.Many2many('res.users', string='SalesPerson', compute='_compute_allowed')
    @api.onchange('team_id')
    def _compute_allowed(self):
        for this in self:
            this.allowed_members = [(5,0,0)]
            # for team in this.team_ids:
            this.allowed_members = [(4,user.id) for user in this.team_id.member_ids]


    date_start = fields.Date(string='Start Date',default=time.strftime('2025-01-01'))
    date_end = fields.Date(string='End Date')



    def get_account_statement_total_report(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError("The end date cannot be greater than the start date.")
        if self.partner_id:
            moves = self.env['account.move.line'].search([('partner_id','=',self.partner_id.id),'|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('parent_state', '=', 'posted')])
        else:
            if self.team_id and not self.user_ids:
                print('wwwwww')
                moves = self.env['account.move.line'].search([('partner_id.team_id','=',self.team_id.id),'|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('parent_state', '=', 'posted')])

            else:
                moves = self.env['account.move.line'].search([('partner_id.user_id.id','in',self.user_ids.ids),'|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('parent_state', '=', 'posted')])

        
        if self.date_start and not self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start)

        elif not self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date <= self.date_end)
        elif self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start and x.date <= self.date_end)
        else:
            all_record = moves
        
        if not all_record:
            raise UserError(_('No Posted Entries'))

        return self.env.ref('account_statment.action_report_account_statment_total_layout').report_action(all_record)