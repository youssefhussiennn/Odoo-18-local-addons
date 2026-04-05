# -*- coding: utf-8 -*-
{
    'name': "add_analytic_account_in_expense_by_default",

    'summary': """
        Get analytic account from employee for expenses""",

    'description': """
        Get analytic account from employee for expenses
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Hr',
    'license': 'OPL-1',
    'version': '15.0',
    'depends': ['hr', 'hr_expense'],

    'data': [
        'views/views.xml',
    ],
}
