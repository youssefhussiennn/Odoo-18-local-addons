{
    'name': 'SMSMisr Connector v2',
    'version': '1.0.0',
    'summary': 'Send SMS via SMSMisr from Odoo - messages, config, DLR, test connection',
    'description': 'Connector to send SMS using SMSMisr API. Includes config (singleton), message queue, send service, DLR endpoint and test connection.',
    'author': 'Youssef',
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/smsmisr_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
