{
    'name': 'Operation Visits',
    'version': '18.0.1.8.1',
    'summary': 'Customer visits for operations team: follow up, return, collection',
    'category': 'Operations',
    'author': 'Atlas for Agricultural Development',
    'license': 'LGPL-3',
    'depends': ['mail', 'account', 'hr', 'hr_attendance_portal'],
    'data': [
        'security/operation_visit_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/operation_visit_views.xml',
        'views/operation_visit_expense_views.xml',
        'views/hr_employee_views.xml',
        'views/portal_templates.xml',
        'views/menus.xml',
        'report/operation_visit_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'atlas_operation_visits/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
