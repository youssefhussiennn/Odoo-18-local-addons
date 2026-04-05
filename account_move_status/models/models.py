from odoo import models, fields

class AccountMove(models.Model):
    _inherit = ("account.move")

    new_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('pass', 'Pass'),
    ], string='New Status', readonly=True, copy=False, default='in_progress', tracking=True)


    def action_set_status_pass(self):
        for record in self:
            record.new_status = 'pass'