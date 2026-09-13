from odoo import models, fields, api


class GraphicsEvent(models.Model):
    _name = 'graphics.event'
    _description = 'Graphics Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Event Title', required=True, tracking=True)
    event_date = fields.Date(string='Event Date', required=True, tracking=True)
    description = fields.Html(string='Description')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'graphics_event_attachment_rel',
        'event_id',
        'attachment_id',
        string='Attachments (PDF)',
    )
    attachment_count = fields.Integer(
        string='Attachments', compute='_compute_attachment_count'
    )

    state = fields.Selection([
        ('draft', 'Planned'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
