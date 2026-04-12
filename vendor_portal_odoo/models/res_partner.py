# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    """Class used to add field to res.partner for differentiate
     registered vendors"""
    _inherit = 'res.partner'

    is_registered = fields.Boolean("Is Registered Vendor", default=False,
                                   help="To denote the is the partner is "
                                        "registered as vendor")
