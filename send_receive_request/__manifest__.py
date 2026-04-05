{
    'name': 'Send & Receive Request',
    'version': '18.0',
    'author': 'Roaya',
    'license': 'AGPL-3',
    'website': 'https://www.roayadm.com',
    'category': 'Accounting',
    'summary': 'Send & Receive Request',
    'depends': ['account_reports', 'account','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/view.xml',
        'views/general_ledger.xml',
    ],
    'installable': True,
}
