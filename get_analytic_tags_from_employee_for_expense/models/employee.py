# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', 'hr_employee_base_account_analytic_tag_rel',
        'employee_id', 'tag_id',string="Analytic Tags")
    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'hr_employee_base_account_analytic_acc_rel',
        'employee_id', 'account_id',
        string="Analytic Accounts")