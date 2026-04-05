# -*- coding: utf-8 -*-
###############################################################################
#

{
    'name': "Restrict Account type for Users",
    "version": "18.0",
    "category": "Accounting",
    "summary": "User can select only allowed Account Types",
    "description": 'Restrict account types for the specific users to access'
                   ' allowed account types only',
    'author': 'Youssef Hussien',
    'company': '',
    'maintainer': '',
    'website': "",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_user_views.xml',
        'views/res_users_account_type_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
