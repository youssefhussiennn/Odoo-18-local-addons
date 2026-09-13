from odoo import models, fields, api


class LegalDocument(models.Model):
    _name = 'legal.document'
    _description = 'Company Legal Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', readonly=True, copy=False, default='New'
    )
    title = fields.Char(string='Document Title', required=True, tracking=True)

    document_type = fields.Selection([
        ('contract', 'Contract'),
        ('license', 'License'),
        ('legal_notice', 'Legal Notice'),
        ('power_of_attorney', 'Power of Attorney'),
        ('other', 'Other'),
    ], string='Document Type', required=True, tracking=True)

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
        'legal_document_attachment_rel',
        'document_id',
        'attachment_id',
        string='Attachments',
    )
    attachment_count = fields.Integer(
        string='Attachments', compute='_compute_attachment_count'
    )

    # ── Computed ──────────────────────────────────────────────────────────────
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'legal.document'
                ) or 'New'
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_archive_document(self):
        self.write({'state': 'archived'})

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachments',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
        }

    # ── Scheduled action: auto-expire ─────────────────────────────────────────
    @api.model
    def _cron_check_expiry(self):
        today = fields.Date.today()
        expired = self.search([
            ('expiry_date', '<', today),
            ('state', '=', 'active'),
        ])
        expired.write({'state': 'expired'})
