# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ro_sales_person = fields.Many2one(string='Journal Entry Sales Person', related='move_id.invoice_user_id', store=True, readonly=False)
    ro_sales_team = fields.Many2one(string='Journal Entry Sales Team', related='move_id.team_id', store=True, readonly=False)
