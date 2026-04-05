# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    required_meter_reading = fields.Boolean(string ="Meter Reading Required") 
    required_servicing = fields.Boolean(string ="Car Servicing Required") 

class HrExpense(models.Model):
    _inherit = 'hr.expense.sheet'


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    required_meter_reading = fields.Boolean(related='product_id.required_meter_reading')
    required_servicing = fields.Boolean(related='product_id.required_servicing')
    meter_reading = fields.Float(string="Meter Reading ", digits=(16,0)) 
    servicing_from = fields.Float(string="From") 
    servicing_to = fields.Float(string="To") 
    servicing_rate = fields.Float(string="Rate") 
    # meter_reading_total = fields.Float(string="Meter Reading") 

    @api.onchange('servicing_from', 'servicing_to', 'servicing_rate')
    def _get_total_currency(self):
        for rec in self:
            if rec.servicing_to and rec.servicing_from and rec.servicing_rate:
                rec.total_amount = (rec.servicing_to - rec.servicing_from) * rec.servicing_rate

