from odoo import models, fields, api
from odoo.exceptions import ValidationError


class OwnerTravel(models.Model):
    _name = 'owner.travel'
    _description = 'Owner Travel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'
    _rec_name = 'title'

    title = fields.Char(string='Travel Title', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Scheduled'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    start_datetime = fields.Datetime(string='Departure', required=True, tracking=True)
    stop_datetime = fields.Datetime(string='Return', required=True, tracking=True)
    duration = fields.Float(
        string='Duration (hrs)', compute='_compute_duration', store=True
    )

    destination = fields.Char(string='Destination', tracking=True)
    transportation = fields.Selection([
        ('flight', 'Flight'),
        ('car', 'Car'),
        ('train', 'Train'),
        ('other', 'Other'),
    ], string='Transportation', default='flight', tracking=True)
    description = fields.Html(string='Notes')

    secretary_id = fields.Many2one(
        'res.users',
        string='Managed by',
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.depends('start_datetime', 'stop_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.stop_datetime:
                delta = rec.stop_datetime - rec.start_datetime
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0.0

    @api.constrains('start_datetime', 'stop_datetime')
    def _check_dates(self):
        for rec in self:
            if rec.start_datetime and rec.stop_datetime:
                if rec.stop_datetime <= rec.start_datetime:
                    raise ValidationError('Return time must be after departure time.')

    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
