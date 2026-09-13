from odoo import models, fields


class SecretaryTimetableWizard(models.TransientModel):
    _name = 'secretary.timetable.wizard'
    _description = 'Print Secretary Timetable'

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
            'secretary_meetings.action_report_timetable'
        ).report_action(self)
