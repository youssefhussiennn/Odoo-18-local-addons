# -*- coding: utf-8 -*-

from odoo import models, fields, _

class ResCompany(models.Model):

    _inherit = 'res.company'

    active = fields.Boolean(string='Active', default=True)
    