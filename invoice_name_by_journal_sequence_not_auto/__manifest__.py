# -*- coding: utf-8 -*-

{
    'name' : 'Invoice Name By Journal Sequence Not Auto',
    'version' : '18.0.0.0',
    'sequence': 201,
    'category': 'Accounting/Accounting',
    'website' : '',
    'license': 'OPL-1',
    'summary' : 'Invoice Name By Journal Sequence Not Auto',
    'description' : """
        Invoice Name By Journal Sequence Not Auto 
    """,
    'depends': [
        'accountant',
    ],
    'data': [
        'views/journal.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}