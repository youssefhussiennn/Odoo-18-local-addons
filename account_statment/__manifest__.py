# -*- coding: utf-8 -*-
{
    'name': "account_statment",

    'summary': """
        Add account statement report""",

    'description': """
        Add account statement report
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Accounting',
    'license': 'OPL-1',
    'version': '18.0',
    'depends': ['account', 'account_followup','sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/account.xml',
        'views/account_move.xml',
        'wizard/account_statement_team.xml',
        'wizard/account_statement.xml',
        'wizard/account_statement_total.xml',
        'wizard/final_account_statement_for_team.xml',
        # 'views/views.xml',
        'views/templates.xml',
        'views/account_statement_total_pdf.xml',
        'views/account_statement_total_pdf2.xml',
        'views/account_statement_team_pdf.xml',
        'views/account_statement_analytic_account.xml',
    ],
}
