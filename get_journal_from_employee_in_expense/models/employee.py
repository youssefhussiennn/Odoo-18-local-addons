# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    journal_id = fields.Many2one('account.journal', string="Journal")
