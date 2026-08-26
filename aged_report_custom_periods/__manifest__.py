{
    'name': 'Aged Report Custom Periods',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Custom aging buckets on Aged Receivable/Payable: 1-30, 31-90, 91-150, 151-365, Older',
    'author': 'Joe',
    'depends': ['account_reports'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'aged_report_custom_periods/static/src/aged_partner_balance_filters_patch.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
