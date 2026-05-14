# -*- coding: utf-8 -*-
{
    'name': "Aged Receivable Salesperson Filter",
    'summary': "Add Salesperson Filter for Aged Receivable Report",
    'description': "Add Salesperson Filter for Aged Receivable Report",
    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'OPL-1',
    'depends': ['account_reports'],
    'assets': {
        'web.assets_backend': [
            'aged_receivable_sp_filter/static/src/components/**/*',
        ],
    },
}
