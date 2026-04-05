# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_commission(models.Model):
    _name = "sale.commission"
    _description = "Sale Commission"

    name = fields.Char(string="Name")
