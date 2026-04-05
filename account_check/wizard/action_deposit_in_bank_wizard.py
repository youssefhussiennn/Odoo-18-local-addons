# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ActionHanded(models.TransientModel):
    _name = 'action.handed.wizard'

    employee_id = fields.Many2one(comodel_name='res.partner', string='Handed To')
    check_id = fields.Many2one(comodel_name='account.check')

    def change_state_to_handed(self):
        selected_ids = self.env.context.get('active_ids', [])
        activity_data = self.env['account.check'].search([('id','in',selected_ids)])
        for check in activity_data:
            if check:
                for line in check.operation_ids:
                    if line.operation == 'holding':
                        line.handed_to = self.employee_id.id
                check.action_to_handed()
