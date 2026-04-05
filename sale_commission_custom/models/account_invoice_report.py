# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    commission_percentage_amount = fields.Float(string="Commission Amount", digits=(16,6), store=True)
    commission_percentage = fields.Float(string="Commission Percentage", digits=(16,6), store=True)
    commission_type = fields.Char(string="Commission Type", store=True)
    commission_state = fields.Selection(
            string='Commission State',
            selection=[('paid', 'Paid'), ('not_paid', 'Not Paid')], 
            default='not_paid'
            
        )



    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ",commission.name as commission_type,move.commission_percntage as commission_percentage\
            , ABS(sum((line.balance * currency_table.rate *move.commission_percntage)/100)) as commission_percentage_amount,\
                move.commission_state as commission_state"

    def _from(self):
        return super(AccountInvoiceReport, self)._from() + "LEFT JOIN sale_commission commission ON commission.id = move.commission_id" 

    def _where(self):
        return super(AccountInvoiceReport, self)._where() + \
               """
               GROUP BY 
               line.id, move.state,move.move_type,move.partner_id,move.invoice_user_id, 
               move.fiscal_position_id,move.payment_state,move.invoice_date,move.invoice_date_due,
               uom_template.id,template.categ_id, uom_line.factor , currency_table.rate, partner.country_id,
               commercial_partner.country_id, move.team_id, move.commission_id, commission.id, move.commission_percntage, move.commission_state
               """


    # def _group_by(self):
    #     return """
    #     GROUP BY line.discount_fixed_amount
    #     """
