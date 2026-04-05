# -*- coding: utf-8 -*-

from odoo import models,fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sales_person = fields.Many2one('res.users',string="Sales Person",related="partner_id.user_id")