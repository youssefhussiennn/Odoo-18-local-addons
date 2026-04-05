# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api


class GeneralLedgerPrint(models.AbstractModel):
    _name = 'report.general_ledger_print_layout.general_ledger_print'

    @api.model
    def _get_report_values(self, docids, data=None):
        # print(data)
        print('kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        # print(data['partner_ids'][0].name)
        # print(docids)

        # date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        # date_end = datetime.strptime(data['date_end'], '%Y-%m-%d').date()

        # moves = []
        # if data['full_report']:
        #     moves = get_full_partner_report(self, date_start, date_end)
        # else:
        #     for id in data['partner_ids']:
        #         moves.append(get_partner_report(self, id, date_start, date_end))
        print(type(data['printed_fields']))
        print(type(data['partner_ids']))
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'partner_ids': self.env['account.move.line'].search([('id', 'in', data['partner_ids'])]),
            'printed_fields':self.env['ir.model.fields'].search([('id', 'in', data['printed_fields'])]),
            'docs': docids,
        }
