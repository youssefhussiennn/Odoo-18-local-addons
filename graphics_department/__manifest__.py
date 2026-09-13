{
    'name': 'Graphics Department',
    'version': '18.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Manage events, scheduled social posts, and CRM clients / potential clients',
    'depends': ['base', 'mail', 'crm'],
    'external_dependencies': {
        'python': ['reportlab'],
    },
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/post_schedule_wizard_views.xml',
        'views/event_views.xml',
        'views/scheduled_post_views.xml',
        'views/crm_client_views.xml',
        'views/menu.xml',
        'report/post_schedule_report_action.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
