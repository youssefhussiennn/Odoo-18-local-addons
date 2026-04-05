# -*- coding: utf-8 -*-
{
    'name': "Analytic tag filter general ledger",
    'summary': "Add analytic tags to General Ledger",
    'description': "Add analytic tags to General Ledger",
    'author': "Youssef Hussien",
    'website': "",
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'OPL-1',
    'depends': ['account_reports'],
    'assets': {
        'web.assets_backend': [
            'analytic_tag_filter_general_ledger/static/src/components/**/*',
        ],
    },
}
