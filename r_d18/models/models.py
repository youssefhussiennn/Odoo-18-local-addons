# -*- coding: utf-8 -*-

from odoo import models, fields, api


class r_d(models.Model):
    _name = 'details'
    _description = 'R&D'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string="Active", default=True, required=True,tracking=True)
    name = fields.Char(string="Product Name",tracking=True, required=True)
    vendor_name = fields.Many2one('res.partner', string="Vendor",tracking=True, required=True)
    company_id = fields.Many2one('res.company', string="Company",tracking=True, required=True)
    locked = fields.Boolean(string="Locked",tracking=True)
    memo = fields.Char(string="Memo",tracking=True)
    product_category = fields.Many2one('product.category', string="Product Category",tracking=True, required=True)
    sequence = fields.Integer(string="Sequence",tracking=True)
    statue = fields.Selection([('draft', 'Draft'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)
    user_id = fields.Many2one('res.users', string="Responsible",tracking=True)
    
    def action_reset(self):
        self.write({'statue': 'draft'})
        self.write({'locked': False})
        
    def action_confirm(self):
        self.write({'statue': 'Approved'})
        self.write({'locked': True})

    def action_reject(self):
        self.write({'statue': 'Rejected'})
        self.write({'locked': True})
    
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