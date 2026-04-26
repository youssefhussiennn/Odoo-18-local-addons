# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class develop_vendor(models.Model):
    _name = 'develop_vendor.develop_vendor'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Develop Vendor'
    
    active = fields.Boolean(string="Active", default=True)
    name = fields.Char("Company Name", required=True, tracking=True)
    responsible_user = fields.Many2one('res.users', string='Responsible User', tracking=True)
    accounting_vendor = fields.Many2one('res.partner', string='Accounting Vendor', tracking=True, readonly=True)
    contact_person = fields.Char("Contact Person", tracking=True)
    contact_position = fields.Char("Contact Position", tracking=True)
    email = fields.Char("Email", tracking=True)
    street = fields.Char("Street")
    City = fields.Char("City")
    country = fields.Many2one('res.country', string='Country')
    other_country = fields.Many2one('res.country', string='Other Branch Country')
    factory_country = fields.Char("Factorty Country")
    website = fields.Char("Website")
    whatsapp = fields.Char("Whatsapp Number")
    we_chat = fields.Char("WeChat Number")
    telephone = fields.Char("Telephone Number")
    Fax = fields.Char("Fax")
    Catalogue = fields.Binary("Catalogue")
    notes = fields.Text("Notes")
    contact_details = fields.One2many('develop_vendor.contact', 'vendor_id', string='Contact Details')
    meeting_points = fields.One2many('develop_vendor.meeting_point', 'vendor_id', string='Meeting Points')
    waiting_icama = fields.One2many('develop_vendor.icama_line', 'vendor_id', string='Waiting ICAMA')
    
    is_supplier = fields.Boolean(string="Supplier",tracking=True)
    is_customer = fields.Boolean(string="Customer",tracking=True)

    description = fields.Text()
    
    vendor_tags = fields.Many2many(
    'develop_vendor.vendor_tag',
    'develop_vendor_tag_rel',
    'vendor_id',
    'tag_id',
    string='Vendor Tags'
    ,tracking=True
    )
    production_field = fields.Many2many(
    'develop_vendor.production_field',
    'develop_vendor_production_rel',
    'vendor_id',
    'production_id',
    string='Production Fields',
    tracking=True
    )
    
    locked = fields.Boolean(string="Locked",tracking=True)
    
    states = fields.Selection([('draft', 'Draft'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    
    
    # Boolean fields
    attended = fields.Boolean(string="Attended")
    predicted_icama = fields.Boolean(string="Predicted ICAMA")
    price_offer = fields.Boolean(string="Price Offer")
    send_documents = fields.Boolean(string="Send Documents")
    waiting_samples = fields.Boolean(string="Waiting Samples")
    fertilizers_sample_test = fields.Boolean(string="Fertilizers Sample Test")

    # Char fields
    predicted_icama_text = fields.Char(string="Predicted ICAMA Text")
    price_offer_text = fields.Char(string="Price Offer Text")
    send_documents_text = fields.Char(string="Send Documents Text")
    waiting_samples_text = fields.Char(string="Waiting Samples Text")
    fertilizers_sample_text = fields.Char(string="Fertilizers Sample Text")

    # Many2many field
    selected_products = fields.Many2many(
        comodel_name='x_details', 
        string="Selected Products"
    )
    
    def action_reset(self):
        self.write({'states': 'draft'})
        self.write({'locked': False})
        
    def action_confirm(self):
        self.write({'states': 'Approved'})
        self.write({'locked': True})

    def action_reject(self):
        self.write({'states': 'Rejected'})
        self.write({'locked': True})

    rd_count = fields.Integer(compute='compute_count_rd')

        
    def compute_count_rd(self):
        for record in self:
            record.rd_count = self.env['x_details'].search_count([
                ('x_studio_vendor', '=', record.id)
            ])
            
    def action_view_rd(self):
        """Smart button action to view RD linked to this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'R&D',
            'res_model': 'x_details',
            'view_mode': 'list,form',
            'domain': [('x_studio_vendor', '=', self.id)],
            'context': {'default_x_studio_vendor': self.id},
        }

class DevelopVendorContact(models.Model):
    _name = 'develop_vendor.contact'
    _description = 'Vendor Contact Details'

    vendor_id = fields.Many2one('develop_vendor.develop_vendor', string='Vendor', ondelete='cascade')
    name = fields.Char("Contact Name", required=True)
    position = fields.Char("Position")
    phone = fields.Char("Phone")
    email = fields.Char("Email")
    notes = fields.Text("Notes")
    
class DevelopVendorMeetingPoint(models.Model):
    _name = 'develop_vendor.meeting_point'
    _description = 'Vendor Meeting Points'

    vendor_id = fields.Many2one('develop_vendor.develop_vendor', string='Vendor', ondelete='cascade')
    description = fields.Text("Description")
    points = fields.Char("Points")
    date = fields.Datetime("Date & Time")
    Attachment = fields.Binary("Attachment")
    
class VendorTag(models.Model):
    _name = 'develop_vendor.vendor_tag'
    _description = 'Vendor Tag'

    name = fields.Char(string='Tag Name', required=True)
    
class ProductionField(models.Model):
    _name = 'develop_vendor.production_field'
    _description = 'Production Field'

    name = fields.Char(string="Name", required=True)


class DevelopVendorIcamaLine(models.Model):
    _name = 'develop_vendor.icama_line'
    _description = 'Vendor Waiting ICAMA Line'

    vendor_id = fields.Many2one('develop_vendor.develop_vendor', string='Vendor', ondelete='cascade', required=True)
    product = fields.Char(string='Product Name')
    date = fields.Date(string='Date')
