# -*- coding: utf-8 -*-

from odoo import models, fields, _

class Website(models.Model):

    _inherit = 'website'

    active = fields.Boolean(string='Active', default=True)
    