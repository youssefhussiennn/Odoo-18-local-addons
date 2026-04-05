# -*- coding: utf-8 -*-
{
    'name': "Account Move Status",

    'summary': """
        Adding a new status for the invoices""",

    'description': """
        Adding a new status for the invoices
    """,

    'author': "Youssef",
    'website': "",


    'category': 'Uncategorized',
    'version': '18.0',

    'depends': ['base','account'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        
    ],
}
