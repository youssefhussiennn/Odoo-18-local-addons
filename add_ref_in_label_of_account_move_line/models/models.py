# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move'


    @api.onchange('ref')
    def get_move_ref(self):
        for rec in self:
            for line in rec.line_ids:

                if rec.ref:
                    line.name = rec.ref