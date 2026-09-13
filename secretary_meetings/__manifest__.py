{
    'name': 'Secretary Meetings',
    'version': '18.0.3.0.0',
    'category': 'Productivity',
    'summary': 'Manage owner meetings, travels and conferences with a bilingual (Arabic/English) printable timetable',
    'depends': ['base', 'mail', 'calendar'],
    'external_dependencies': {
        'python': ['reportlab', 'arabic_reshaper', 'bidi'],
    },
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/meeting_views.xml',
        'views/travel_views.xml',
        'views/conference_views.xml',
        'wizard/timetable_wizard_views.xml',
        'views/menu.xml',
        'report/timetable_report_action.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
