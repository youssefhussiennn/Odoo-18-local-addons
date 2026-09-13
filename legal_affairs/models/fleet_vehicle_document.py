from odoo import models, fields, api


class FleetVehicleDocument(models.Model):
    _name = 'fleet.vehicle.document'
    _description = 'Vehicle Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc'
    _rec_name = 'title'

    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', required=True,
        ondelete='cascade', tracking=True
    )
    title = fields.Char(string='Document Title', required=True, tracking=True)

    document_type = fields.Selection([
        ('registration', 'Registration (License Plate)'),
        ('insurance', 'Insurance'),
        ('inspection', 'Technical Inspection'),
        ('ownership', 'Ownership / Contract'),
        ('other', 'Other'),
    ], string='Document Type', required=True, default='other', tracking=True)

    issue_date = fields.Date(string='Issue Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    ], string='Status', default='active', tracking=True)

    notes = fields.Text(string='Notes')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'fleet_vehicle_document_attachment_rel',
        'document_id',
        'attachment_id',
        string='Attachments',
    )
    attachment_count = fields.Integer(
        string='Attachments', compute='_compute_attachment_count'
    )

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def action_archive_document(self):
        self.write({'state': 'archived'})

    def action_set_active(self):
        self.write({'state': 'active'})

    @api.model
    def _cron_check_expiry(self):
        today = fields.Date.today()
        expired = self.search([
            ('expiry_date', '<', today),
            ('state', '=', 'active'),
        ])
        expired.write({'state': 'expired'})
