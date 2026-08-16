# -*- coding: utf-8 -*-

from odoo import api, models, _, fields
from odoo.exceptions import UserError
import datetime


class Tax2TempalteReport(models.AbstractModel):
    _name = "report.account_statment.action_report_account_statment_total_layout2"
    _description = "Tax 2 Template Report"

    @api.model
    def _get_report_values(self, docids, data):

        currency_id = self.env.company.currency_id.id
        
        print("CALLED")

        return {
            "doc_ids": docids,
            "doc_model": "hr.payslip.line",
            "data": data,
            'currency_id': currency_id,
        }
