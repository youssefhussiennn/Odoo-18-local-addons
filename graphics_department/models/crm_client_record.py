from odoo import models, fields, api


class CrmClientRecord(models.Model):
    _name = 'crm.client.record'
    _description = 'Client / Potential Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    _rec_name = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    whatsapp = fields.Char(string='WhatsApp Number', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Address')
    notes = fields.Text(string='Notes')

    client_type = fields.Selection([
        ('potential', 'Potential Client'),
        ('client', 'Client'),
    ], string='Type', default='potential', required=True, tracking=True)

    converted_date = fields.Date(string='Converted On', readonly=True, copy=False)

    def action_convert_to_client(self):
        self.write({
            'client_type': 'client',
            'converted_date': fields.Date.today(),
        })
