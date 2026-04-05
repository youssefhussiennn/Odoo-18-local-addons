# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")

# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'

#     analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")

