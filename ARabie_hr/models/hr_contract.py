# -*- coding: utf-8 -*-
# Copyright (c) Abdulrahman Rabie, AlArabia Group All Rights Reserved
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    # will add extra 8 fields named x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8
    x_1 = fields.Monetary('Parameter 1', default=0,  tracking=True,)
    x_2 = fields.Monetary('Parameter 2', default=0,  tracking=True,)
    x_3 = fields.Monetary('Parameter 3', default=0,  tracking=True,)
    x_4 = fields.Monetary('Parameter 4', default=0,  tracking=True,)
    x_5 = fields.Monetary('Parameter 5', default=0,  tracking=True,)
    x_6 = fields.Monetary('Parameter 6', default=0,  tracking=True,)
    x_7 = fields.Monetary('Parameter 7', default=0,  tracking=True,)
    x_8 = fields.Monetary('Parameter 8', default=0,  tracking=True,)
    

