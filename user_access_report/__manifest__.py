# -*- coding: utf-8 -*-
{
    'name': "User Access Export",

    'summary': """
        Export CRUD permissions of selected users on chosen models""",

    'description': """
        Export CRUD permissions of selected users on chosen models
    """,

    'author': "Youssef",
    'website': "",


    'category': 'Uncategorized',
    'version': '0.1',
    "application": False,
    'depends': ['base'],

    'data': [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "wizard/user_access_wizard_views.xml",
        # "reports/user_access_report_templates.xml",  
        
    ],
}
