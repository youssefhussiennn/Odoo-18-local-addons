from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    investigation_ids = fields.One2many(
        'legal.investigation', 'employee_id', string='Investigations'
    )
    investigation_count = fields.Integer(
        string='Investigations', compute='_compute_investigation_count'
    )

    @api.depends('investigation_ids')
    def _compute_investigation_count(self):
        for emp in self:
            emp.investigation_count = len(emp.investigation_ids)

    def action_open_investigations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Investigations',
            'res_model': 'legal.investigation',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
