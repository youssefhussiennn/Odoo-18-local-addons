# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    complete_address = fields.Char(string="Complete Address", related='partner_id.contact_address')
    phone = fields.Char(string="Phone", related="partner_id.phone")
    mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    sales_team_id = fields.Many2one('crm.team', string="Sales Team", related="sale_id.team_id")
    salesperson_id = fields.Many2one('res.users', string="Salesperson", related="partner_id.user_id")
    created_by_id = fields.Many2one('res.users', related="sale_id.create_uid")
