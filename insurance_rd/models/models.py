# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class r_d(models.Model):
    _name = 'details'
    _description = 'Insurance Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string="Active", default=True, required=True,tracking=True)
    name = fields.Char(string="Serial Number",tracking=True)
    customer_name = fields.Many2one('res.partner', string="Customer",tracking=True, required=True)
    locked = fields.Boolean(string="Locked",tracking=True)
    notes = fields.Html(string="Notes",tracking=True)
    statue = fields.Selection([('draft', 'Draft'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)
    user_id = fields.Many2one('res.users', string="Responsible",tracking=True)
    contact_details = fields.One2many('contact', 'name', string='Insurance Contact Details')
    vessel_id = fields.Many2one(
            'vessels_management.vessels_management',
            string="Vessel",
            domain="[('vessel_owner_id', '=', customer_name)]",
            help="Select the vessel owned by this customer."
        )
    sales_count = fields.Integer(string="Sales Orders",store=True)
    def action_reset(self):
        self.write({'statue': 'draft'})
        self.write({'locked': False})
        self.write({'sales_count': 0})
        
    def action_confirm(self):
        self.write({'statue': 'Approved'})
        self.write({'locked': True})

    def action_reject(self):
        self.write({'statue': 'Rejected'})
        self.write({'locked': True})

    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('details.serial') or 'New'
        return super(r_d, self).create(vals)
    
    @api.onchange('customer_name')
    def _onchange_customer_name(self):
        """Filter vessels by selected customer."""
        for order in self:
            if not order.customer_name:
                order.vessel_id = False
            else:
                # Reset vessel if it doesn't belong to new partner
                if order.vessel_id and order.vessel_id.vessel_owner_id != order.customer_name:
                    order.vessel_id = False    
                    
    def action_quotations_view(self):
        
        if not self.customer_name:
            raise UserError(_('Please select a "Customer".'))

        # find approved contact
        approved_contact = self.contact_details.filtered(lambda c: c.states == 'approve')

        if not approved_contact:
            raise UserError(_('No approved contact details found.'))

        # if multiple, just pick the first one
        contact = approved_contact[0]
        self.write({'sales_count': 1}) 
        sale_order = self.env['sale.order'].create({
            'partner_id': contact.insurance_company_name.id,  # insurance company as customer
            'person_in_charge': self.user_id.id,
            'state': 'draft',
            'note': self.notes,
            'vessel_id': self.vessel_id.id if self.vessel_id else False,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Quotation Created'),
                'message': _('Quotation %s has been successfully created for %s.') % (
                    sale_order.name, contact.insurance_company_name.name),
                'sticky': False,
                'type': 'success',
  
                
            },
        }
        

class RdContact(models.Model):
    _name = 'contact'
    _description = 'Vendor Contact Details'

    name= fields.Many2one('details', string='Insurance Detail', ondelete='cascade')
    insurance_company_name = fields.Many2one('res.partner', string='Insurance Company', required=True,tracking=True)
    phone = fields.Char(related='insurance_company_name.phone', string="Phone", store=True, readonly=True)
    email = fields.Char(related='insurance_company_name.email', string="Email", store=True, readonly=True)
    notes = fields.Text("Notes")
    states = fields.Selection([('on_going', 'On Going'),('pending', 'Pending'),('cancel', 'Canceled'),('approve', 'Approved')], string='Status', default='on_going', tracking=True)
    
class XDeals(models.Model):
    _name = 'deals'
    _description = 'Deals'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string="Active", default=True,tracking=True)
    name = fields.Char(string="Prodct Name",tracking=True, required=True)
    company_id = fields.Many2one('res.company', string="Company",tracking=True, required=True)
    confirm_date = fields.Date(string="Confirm Date")
    currency_id = fields.Many2one('res.currency', string="Currency")
    custom_agrement = fields.Boolean(string="Custom Agreement")
    product_id = fields.Many2one('product.product', string="Confirmed Product")
    memo = fields.Char(string="Memo")
    price = fields.Float(string="Price")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string="Priority",tracking=True, required=True, default='0')
    product_category = fields.Many2one('product.category', string="Product Category")
    sequence = fields.Integer(string="Sequence")
    state = fields.Selection([('New', 'New'),
        ('run', 'Run'),
        ('close', 'Close')
    ], string="State",default='New', tracking=True)
    user_id = fields.Many2one('res.users', string="Responsible")
    value = fields.Float(string="Value")
    vendor = fields.Many2one('res.partner', string="Vendor",tracking=True, required=True)

    def action_run(self):
        self.write({'state': 'run'})

    def action_close(self):
        self.write({'state': 'close'})
