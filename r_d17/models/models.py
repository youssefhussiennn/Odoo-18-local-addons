# -*- coding: utf-8 -*-

from odoo import models, fields, api


class r_d(models.Model):
    _name = 'x_details'
    _description = 'R&D'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Product Name", required=True)
    com_name = fields.Char(string="Commercial Name")
    function = fields.Char(string="Function")
    x_registration_number = fields.Char(string="رقم التسجيل")
    x_studio_company_id = fields.Many2one('res.company', string="Company")
    x_studio_crop = fields.Char(string="Crop")
    x_studio_locked = fields.Boolean(string="Locked")
    x_studio_material = fields.Char(string="Material", readonly=True)
    x_studio_memo = fields.Html(string="Memo")
    x_studio_momemo = fields.Char(string="momemo")
    x_studio_pests = fields.Char(string="Pests")
    x_studio_product_category = fields.Many2one('product.category', string="Product Category")
    x_studio_qtyyear = fields.Integer(string="QTY/Year")
    x_studio_regestraion = fields.Selection([
        ('مسجل', 'مسجل'), 
        ('غير مسجل', 'غير مسجل'),
    ], string="Registration")
    x_studio_sample = fields.Selection([
        ('متاح', 'متاح'),
        ('غير متاح', 'غير متاح')
    ], string="Sample")
    x_studio_sequence = fields.Integer(string="Sequence")
    # x_studio_statue = fields.Selection([
    #     ('1', 'Under Research'),
    #     ('5', 'Rejected'),
    #     ('2', '	Waiting Sample'),
    #     ('3', 'Under Registration'),
    #     ('4','Registered')
    # ], string="Status", store=False)
    x_studio_stuff = fields.Many2one('x_stuff', string="Stuff")
    type = fields.Many2many('type','r_d_type_rel','x_name','name', string="Type")
    x_studio_target_comption = fields.Char(string="Target Composition")
    x_studio_usage_rate = fields.Char(string="Usage rate")
    pd = fields.Char(string="PD")
    x_studio_user_id = fields.Many2one('res.users', string="Responsible")
    
    loa = fields.Boolean(string="LOA", default=False)
    coo = fields.Boolean(string="COO (iCama)", default=False)
    coa = fields.Boolean(string="COA", default=False)
    tds = fields.Boolean(string="TDS", default=False)
    
    statue = fields.Selection([
        ('1', 'Under Research'),
        ('2', 'Waiting Sample'),
        ('3', 'Under Registration'),
        ('4','Registered'),
        ('5', 'Rejected'),
    ], string="Status", default='1', tracking=True)
        
    # def action_reset(self):
    #     self.write({'statue': 'draft'})
    #     self.write({'x_studio_locked': False})
        
    # def action_confirm(self):
    #     self.write({'statue': 'Approved'})
    #     self.write({'x_studio_locked': True})

    # def action_reject(self):
    #     self.write({'statue': 'Rejected'})
    #     self.write({'x_studio_locked': True})

class XStuff(models.Model):
    _name = 'x_stuff'
    _description = 'Stuff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    x_active = fields.Boolean(string="Active", default=True)
    x_name = fields.Char(string="Description")
    x_studio_company_id = fields.Many2one('res.company', string="Company")
    x_studio_material = fields.Char(string="Material")
    x_studio_state = fields.Selection([
        ('1', 'مستهدف'),
        ('2', 'تحت التسجيل'),
        ('3', 'مسجل'),
    ], string="State")
    
    
class Type(models.Model):
    _name = 'type'
    _description = 'type'
    _rec_name = 'name'
    
    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name")
    
class XDeals(models.Model):
    _name = 'x_deals'
    _description = 'Deals'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    x_active = fields.Boolean(string="Active", default=True)
    x_name = fields.Char(string="Description")
    x_studio_company_id = fields.Many2one('res.company', string="Company")
    x_studio_composition = fields.Char(string="Composition", readonly=True)
    x_studio_confermed_qty = fields.Float(string="Confirmed Qty")
    x_studio_confirm_date = fields.Date(string="Confirm Date")
    x_studio_currency_id = fields.Many2one('res.currency', string="Currency")
    x_studio_custom_agrement = fields.Boolean(string="Custom Agreement")
    x_studio_many2one_field_EjZeD = fields.Many2one('product.product', string="Product")
    x_studio_momemo = fields.Char(string="Momemo")
    x_studio_price = fields.Float(string="Price")
    x_studio_priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string="Priority")
    x_studio_priority_1 = fields.Selection([
        ('0','A'),
        ('1','A+'),
        ('2','B'),
        ('3','C'),
        ('4','D'),
    ], string="Priority (1)")
    x_studio_product_category = fields.Many2one('product.category', string="Product Category", readonly=True)
    x_studio_regestraion = fields.Selection([
        ('موسم اول', 'موسم اول'),
        ('موسم ثاني', 'موسم ثاني'),
        ('تحكيم', 'تحكيم'),
        ('مسجل', 'مسجل'),
        ('اعادة تقييم','اعادة تقييم')
    ], string="Regestraion", readonly=True)
    x_studio_same = fields.Boolean(string="مطابقه")
    x_studio_sample = fields.Boolean(string="Sample")
    x_studio_selection_field_9z1lz = fields.Selection([
        ('0','Low'),
        ('1','Normal'),
        ('2','High'),
        ('3','Very High')
    ], string="New Priority")
    x_studio_sequence = fields.Integer(string="Sequence")
    x_studio_ship_date = fields.Date(string="Ship Date")
    x_studio_state = fields.Selection([
        ('run', 'Run'),
        ('close', 'Close')
    ], string="State")
    x_studio_stock = fields.Float(string="Stock", readonly=True, store=False)
    x_studio_target_qty = fields.Float(string="Target Qty")
    x_studio_uom = fields.Many2one('uom.uom', string="UOM", readonly=True)
    x_studio_usage_rat = fields.Char(string="Usage Rat", readonly=True)
    x_studio_user_id = fields.Many2one('res.users', string="Responsible")
    x_studio_value = fields.Float(string="Value")
    x_studio_vendor = fields.Many2one('res.partner', string="Vendor")
