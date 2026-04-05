# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    need_approve = fields.Boolean(string="Need Approve")
    responsible = fields.Many2one('res.users', string="Responsible")
