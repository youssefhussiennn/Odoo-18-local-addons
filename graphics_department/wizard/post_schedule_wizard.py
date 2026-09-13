from odoo import models, fields


class PostScheduleWizard(models.TransientModel):
    _name = 'graphics.post.schedule.wizard'
    _description = 'Print Scheduled Posts Calendar'

    period = fields.Selection([
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ], string='Period', default='week', required=True)
    date_ref = fields.Date(
        string='Reference Date', default=fields.Date.context_today, required=True
    )

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'graphics_department.action_report_post_schedule'
        ).report_action(self)
