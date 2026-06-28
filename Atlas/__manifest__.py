{
    'name': 'Driver Attendance Portal',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Public portal for driver check-in/out with GPS — no login required',
    'author': 'Custom Dev',
    'depends': ['hr_attendance', 'portal', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_portal_template.xml',
        'views/hr_attendance_view_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}