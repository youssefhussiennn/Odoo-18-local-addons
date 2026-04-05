# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move.line'

    partner_sales_person  = fields.Many2one(related='partner_id.user_id', store=True, string="Partner Sales Person")
    # partner_sales_team  = fields.Many2one(related='partner_id.team_id', store=True, string="Partner Sales Team")