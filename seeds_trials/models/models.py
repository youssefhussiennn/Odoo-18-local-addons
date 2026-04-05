# -*- coding: utf-8 -*-

from odoo import models, fields, api


class seeds_trials(models.Model):
    _name = 'seeds_trials'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'seeds_trials.seeds_trials'

    copmany_name = fields.Char(string="Company Name", tracking=True)
    seeds_class = fields.Char(string="Class")
    company_code = fields.Integer(string="Company Code")
    internal_code = fields.Integer(string="Internal Code", tracking=True)
    pic_item = fields.Image(string="Picture Of The Item")
    plantation_type = fields.Selection([('1', 'ارضى'),('2', 'سلك  - صوب & حقل مفتوح '),],string='Plantation Type',required=True)
    cultivation_place = fields.Char(string="Place of cultivation")
    planting_timing = fields.Char(string="Planting Timing")
    competitive_class = fields.Selection([('1', 'مشابه'),('2', 'غير مشابه'),],string='Competitive Class',required=True)
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
    width = fields.Char(string="width")
    temp = fields.Float(string="The appropriate temperature for agriculture")
    sugar_percent = fields.Float(string="Sugar Percentage")
    fertiliz_need = fields.Char(string="Fertilization needs")
    period_of_mature = fields.Char(string="The period of time that the variety needs to mature")
    position_of_class = fields.Char(string="The position of the class", tracking=True)
    price = fields.Monetary(string="Price", currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)

