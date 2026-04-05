# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Partner Ledger Receivable',
    'summary': """
        New partner ledger report with only receivable accounts""",

    'version': '18.0',
    'category': 'account',
    'depends': ['account_reports'],
    'author': "Roaya",
    'website': "http://www.roayadm.com",
    'license': 'OPL-1',
    'data': [
        'data/account_financial_report_data.xml'
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
