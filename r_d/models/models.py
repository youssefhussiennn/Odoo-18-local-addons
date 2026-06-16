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
    priority = fields.Selection([
        ('1', 'Low'), 
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High'),
    ], string="Priority")
    x_studio_sample = fields.Selection([
        ('متاح', 'متاح'),
        ('غير متاح', 'غير متاح')
    ], string="Sample")
    x_studio_sequence = fields.Integer(string="Sequence")
    # x_studio_statue = fields.Selection([
    #     ('1', 'Under Research'),
    #     ('5', 'Rejected'),
    #     ('2', 'Waiting Sample'),
    #     ('3', 'Under Registration'),
    #     ('4','Registered')
    # ], string="Status", store=False)
    x_studio_stuff = fields.Many2one('x_stuff', string="Stuff")
    type = fields.Many2many('type','r_d_type_rel','x_name','name', string="Type")
    x_studio_target_comption = fields.Char(string="Target Composition")
    x_studio_usage_rate = fields.Char(string="Usage rate")
    pd = fields.Char(string="PD")
    x_studio_user_id = fields.Many2one('res.users', string="Responsible")
    
    # === LOA ===
    loa = fields.Boolean(string="LOA", tracking=True)
    loa_pdf = fields.Binary(string="LOA PDF")
    loa_pdf_filename = fields.Char(string="LOA Filename")
    loa_date = fields.Datetime(string="LOA Updated On")

    # === COO ===
    coo = fields.Boolean(string="COO (iCama)", tracking=True)
    coo_pdf = fields.Binary(string="COO PDF")
    coo_pdf_filename = fields.Char(string="COO Filename")
    coo_date = fields.Datetime(string="COO Updated On")

    # === COA ===
    coa = fields.Boolean(string="COA", tracking=True)
    coa_pdf = fields.Binary(string="COA PDF")
    coa_pdf_filename = fields.Char(string="COA Filename")
    coa_date = fields.Datetime(string="COA Updated On")

    # === TDS ===
    tds = fields.Boolean(string="TDS", tracking=True)
    tds_pdf = fields.Binary(string="TDS PDF")
    tds_pdf_filename = fields.Char(string="TDS Filename")
    tds_date = fields.Datetime(string="TDS Updated On")
    
    # === Manufacturing License ===
    manufacturing_license = fields.Boolean(string="Manufacturing License", tracking=True)
    manufacturing_license_pdf = fields.Binary(string="Manufacturing License PDF")
    manufacturing_license_pdf_filename = fields.Char(string="Manufacturing License Filename")
    manufacturing_license_date = fields.Datetime(string="Manufacturing License Updated On")


    # === Manufacturer Product List ===
    manufacturer_product_list = fields.Boolean(string="Manufacturer Product List", tracking=True)
    manufacturer_product_list_pdf = fields.Binary(string="Manufacturer Product List PDF")
    manufacturer_product_list_pdf_filename = fields.Char(string="Manufacturer Product List Filename")
    manufacturer_product_list_date = fields.Datetime(string="Manufacturer Product List Updated On")


    # === Certificate of Composition ===
    coc = fields.Boolean(string="COC (Certificate of Composition)", tracking=True)
    coc_pdf = fields.Binary(string="COC PDF")
    coc_pdf_filename = fields.Char(string="COC Filename")
    coc_date = fields.Datetime(string="COC Updated On")


    # === Quality Guarantee ===
    quality_guarantee = fields.Boolean(string="Quality Guarantee Certificate", tracking=True)
    quality_guarantee_pdf = fields.Binary(string="Quality Guarantee PDF")
    quality_guarantee_pdf_filename = fields.Char(string="Quality Guarantee Filename")
    quality_guarantee_date = fields.Datetime(string="Quality Guarantee Updated On")


    # === Package Guarantee ===
    package_guarantee = fields.Boolean(string="Package Guarantee Certificate", tracking=True)
    package_guarantee_pdf = fields.Binary(string="Package Guarantee PDF")
    package_guarantee_pdf_filename = fields.Char(string="Package Guarantee Filename")
    package_guarantee_date = fields.Datetime(string="Package Guarantee Updated On")


    # === Toxicological Studies ===
    toxicological_studies = fields.Boolean(string="Toxicological Studies", tracking=True)
    toxicological_studies_pdf = fields.Binary(string="Toxicological Studies PDF")
    toxicological_studies_pdf_filename = fields.Char(string="Toxicological Studies Filename")
    toxicological_studies_date = fields.Datetime(string="Toxicological Studies Updated On")


    # === Analytical Method ===
    analytical_method = fields.Boolean(string="Analytical Method", tracking=True)
    analytical_method_pdf = fields.Binary(string="Analytical Method PDF")
    analytical_method_pdf_filename = fields.Char(string="Analytical Method Filename")
    analytical_method_date = fields.Datetime(string="Analytical Method Updated On")


    # === Residue Analysis ===
    residue_analysis = fields.Boolean(string="Residue Analysis Method", tracking=True)
    residue_analysis_pdf = fields.Binary(string="Residue Analysis PDF")
    residue_analysis_pdf_filename = fields.Char(string="Residue Analysis Filename")
    residue_analysis_date = fields.Datetime(string="Residue Analysis Updated On")


    # === Major Impurities Analysis ===
    impurities_analysis = fields.Boolean(string="Major Impurities Analysis", tracking=True)
    impurities_analysis_pdf = fields.Binary(string="Major Impurities Analysis PDF")
    impurities_analysis_pdf_filename = fields.Char(string="Major Impurities Analysis Filename")
    impurities_analysis_date = fields.Datetime(string="Major Impurities Analysis Updated On")


    # === International Classification ===
    international_classification = fields.Boolean(string="International Classification", tracking=True)
    international_classification_pdf = fields.Binary(string="International Classification PDF")
    international_classification_pdf_filename = fields.Char(string="International Classification Filename")
    international_classification_date = fields.Datetime(string="International Classification Updated On")


    # === ADI / MRL ===
    adi_mrl = fields.Boolean(string="ADI / MRL", tracking=True)
    adi_mrl_pdf = fields.Binary(string="ADI / MRL PDF")
    adi_mrl_pdf_filename = fields.Char(string="ADI / MRL Filename")
    adi_mrl_date = fields.Datetime(string="ADI / MRL Updated On")


    # === Safe Handling Storage Application ===
    safe_handling = fields.Boolean(string="Safe Handling Storage Application", tracking=True)
    safe_handling_pdf = fields.Binary(string="Safe Handling PDF")
    safe_handling_pdf_filename = fields.Char(string="Safe Handling Filename")
    safe_handling_date = fields.Datetime(string="Safe Handling Updated On")


    # === MSDS ===
    msds = fields.Boolean(string="MSDS", tracking=True)
    msds_pdf = fields.Binary(string="MSDS PDF")
    msds_pdf_filename = fields.Char(string="MSDS Filename")
    msds_date = fields.Datetime(string="MSDS Updated On")


    # === Other Documents ===
    other_documents = fields.Boolean(string="Other Required Documents", tracking=True)
    other_documents_pdf = fields.Binary(string="Other Required Documents PDF")
    other_documents_pdf_filename = fields.Char(string="Other Required Documents Filename")
    other_documents_date = fields.Datetime(string="Other Required Documents Updated On")
    
    
    statue = fields.Selection([
        ('1', 'Under Research'),
	('6', 'Completing Documents'),
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


    def write(self, vals):
        now = fields.Datetime.now()

        certificate_fields = [
            'loa',
            'coo',
            'coa',
            'tds',
            'manufacturing_license',
            'manufacturer_product_list',
            'coc',
            'quality_guarantee',
            'package_guarantee',
            'toxicological_studies',
            'analytical_method',
            'residue_analysis',
            'impurities_analysis',
            'international_classification',
            'adi_mrl',
            'safe_handling',
            'msds',
            'other_documents'
        ]

        for field in certificate_fields:
            if field in vals:
                vals[field + '_date'] = now

        return super().write(vals)
    
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
