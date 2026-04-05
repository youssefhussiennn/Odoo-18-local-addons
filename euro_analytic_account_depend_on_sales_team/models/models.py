# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CRMTeam(models.Model):
    _inherit = 'crm.team'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Sales Analytic Account")
    payment_analytic_account_id = fields.Many2one('account.analytic.account', string="Payment Analytic Account")
    