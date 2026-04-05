# -*- coding: utf-8 -*-
# Copyright (c) Abdulrahman Rabie, AlArabia Group All Rights Reserved
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'


    employee_pin = fields.Char(string="Employee PIN", help="Employee PIN")
    input_date = fields.Date(string='Input Date',)
    payslip_id = fields.Many2one(
        'hr.payslip', string='Pay Slip', required=False, ondelete='cascade', index=True)
    contract_id = fields.Many2one(related='payslip_id.contract_id', string='Contract', required=False,
        help="The contract for which applied this input")
    code = fields.Char(related='input_type_id.code', required=False,
                       help="The code that can be used in the salary rules", store=True)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', required=True, domain="[]")
    _allowed_input_type_ids = fields.Many2many('hr.payslip.input.type', related='payslip_id.struct_id.input_line_type_ids')