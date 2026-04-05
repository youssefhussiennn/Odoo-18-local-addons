# -*- coding: utf-8 -*-
{
    'name': "general_ledger_print_layout",

    'summary': """
        Print General Ledger """,

    'description': """
        Print General Ledger 
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'license': 'OPL-1',

    'category': 'Account',
    'version': '18.0',
    'depends': ['account', 'base'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/general_ledger_wizard.xml',
        'views/templates.xml',
    ],
}
