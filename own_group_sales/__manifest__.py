# -*- coding: utf-8 -*-
{
    'name': "Own Group Sales",
    'summary': """Sales team manager view own team sales""",
    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Sales',
    'version': '18.0',
    'license': 'OPL-1',
    'depends': ['sales_team', 'sale_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_team.xml',
    ],
    'installable': True,
    'application': False,
}
