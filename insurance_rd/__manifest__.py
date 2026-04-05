# -*- coding: utf-8 -*-
{
    'name': "insurance_rd",

    'summary': "Insurance r&d module",

    'description': """

    """,

    'author': "Youssef",
    'website': "",

    'category': 'Purchase',
    'version': '18.0',


    'depends': ['base','mail','purchase','vessels_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/sequence.xml',
    ],
    'images': ['static/description/menu_icon_rd.png'],
    'application': True,
}

