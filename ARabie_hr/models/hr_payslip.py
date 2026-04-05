# -*- coding: utf-8 -*-
# Copyright (c) Abdulrahman Rabie, AlArabia Group All Rights Reserved
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    def action_payslip_cancel(self):
        super(HrPayslip, self).action_payslip_cancel()
        for line in self.input_line_ids:
            line.payslip_id = False
        
    def unlink(self):
        # for line in self.input_line_ids.filtered(lambda x: not x.loan_line_id or not x.salary_advance_id):
        for line in self.input_line_ids:
            line.payslip_id = False
        return super(HrPayslip, self).unlink()
    def compute_sheet(self):
        
        for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
            
            emp_pin = payslip.employee_id.pin
            not_assigned_inputs = self.env['hr.payslip.input'].sudo().search(
                [('employee_pin', '=', emp_pin), ('input_date', '>=', payslip.date_from), ('input_date', '<=', payslip.date_to),])
            not_assigned_inputs.payslip_id = payslip.id
            
        res = super(HrPayslip, self).compute_sheet()
        return res
