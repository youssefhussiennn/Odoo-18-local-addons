# -*- coding: utf-8 -*-

from odoo import models, fields, api


class seeds(models.Model):
    _name = 'seeds.seeds'
    _description = 'seeds.seeds'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    user_id = fields.Many2one('res.users', string="Responsible User", default=lambda self: self.env.user, tracking=True)
    state = fields.Selection([
    ('under_evaluate', 'Under Evaluate'),
    ('success', 'Success'),
    ('fail', 'Fail'),
    ], string="Status", default='under_evaluate', tracking=True)
    copmany_name = fields.Char(string="Company Name", tracking=True)
    name = fields.Char(string="Class", tracking=True, required=True)
    trade_name = fields.Char(string="Trade Name", tracking=True)
    external_code = fields.Char(string="External Code", tracking=True)
    code = fields.Char(string="Code", tracking=True,required=True)
    pic_item = fields.Image(string="Picture Of The Item")
    plantation_type = fields.Selection([('1', 'ارضى'),('2', 'سلك  - صوب & حقل مفتوح '),],string='Plantation Type', tracking=True)
    cultivation_place = fields.Char(string="Place of cultivation", tracking=True)
    planting_timing = fields.Char(string="Planting Timing", tracking=True)
    competitive_class = fields.Selection([('1', 'مشابه'),('2', 'غير مشابه'),],string='Competitive Class', tracking=True)
    plan = fields.Selection([('1', 'Plan 01'),('2', 'Plan 02'),('3', 'Plan 03'),('4', 'Plan 04'),],string='Plan',tracking=True)
    vegetative_total = fields.Char(string="Vegetative Total")
    productivity_rate = fields.Char(string="Productivity Rate")
    fruit_shape = fields.Char(string="Fruit Shape")
    disease_tolerance = fields.Char(string="Disease tolerance")
    craft = fields.Char(string="The Craft")
    shell_thickness = fields.Char(string="Shell Thickness")
    room_num = fields.Char(string="Number of rooms")
    weight = fields.Char(string="Weight")
    color = fields.Char(string="Color")
    height = fields.Char(string="Height")
    width = fields.Char(string="Width")
    pack = fields.Char(string="Pack")
    comparision = fields.Char(string="Comparison")
    number_of_packets = fields.Char(string="Number Of Packets")
    notes = fields.Text(string="Notes")
    description = fields.Text(string="Description")
    temp = fields.Float(string="The appropriate temperature for agriculture")
    sugar_percent = fields.Float(string="Sugar Percentage")
    fertiliz_need = fields.Char(string="Fertilization needs")
    period_of_mature = fields.Char(string="The period of time that the variety needs to mature")
    position_of_class = fields.Char(string="The position of the class", tracking=True)
    price = fields.Monetary(string="Price", currency_field='currency_id', tracking=True)
    price_kg = fields.Monetary(string="Price per kg", currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    
    
    def action_under_evaluate(self):
        for rec in self:
            rec.state = 'under_evaluate'


    def action_success(self):
        for rec in self:
            rec.state = 'success'


    def action_fail(self):
        for rec in self:
            rec.state = 'fail'