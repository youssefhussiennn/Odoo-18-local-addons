# -*- coding: utf-8 -*-

{
    'name': 'Hide Account Report',
    'version': '15.0',
    'sequence': 201,
    'category': 'Accounting/Accounting',
    'website': '',
    'license': 'OPL-1',
    'summary': 'Hide Account Report',
    'description': """
        Hide Account Report 
    """,
    'depends': [
        'web',
        'account',
        'account_reports',
    ],
    'data': [
        'security/security.xml',
        'views/report.xml',
        'views/account.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
