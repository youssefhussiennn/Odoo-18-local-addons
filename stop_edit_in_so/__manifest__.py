# -*- coding: utf-8 -*-
{
    'name': "stop_edit_in_so",

    'summary': """
        Stop edit in sale order after first approve""",

    'description': """
        Stop edit in sale order after first approve
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Sale',
    'license': 'OPL-1',
    'version': '18.0',

    'depends': ['sale', 'own_group_sales'],

    'data': [
        'views/views.xml',
    ],
}
