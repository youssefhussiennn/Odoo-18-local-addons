from odoo import models, fields, api


class GraphicsScheduledPost(models.Model):
    _name = 'graphics.scheduled.post'
    _description = 'Scheduled Post'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_datetime asc'
    _rec_name = 'title'

    title = fields.Char(string='Post Title', required=True, tracking=True)
    scheduled_datetime = fields.Datetime(
        string='Scheduled Date & Time', required=True, tracking=True
    )
    content = fields.Text(string='Caption / Content')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'graphics_post_attachment_rel',
        'post_id',
        'attachment_id',
        string='Attachments (Image / PDF / Any file)',
    )
    attachment_count = fields.Integer(
        string='Attachments', compute='_compute_attachment_count'
    )

    state = fields.Selection([
        ('draft', 'Scheduled'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def action_mark_posted(self):
        self.write({'state': 'posted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
