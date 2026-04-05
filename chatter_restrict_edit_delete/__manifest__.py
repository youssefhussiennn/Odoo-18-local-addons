{
    'name': 'Restrict chatter Edit and Delete',
    'version': '18.0',
    'summary': 'Restricts editing and deleting log notes in Odoo 18.',
    'description': """
        This module restricts the ability to edit and delete log notes (mail.message) in Odoo 18.
        It includes custom security rules and view modifications to enforce these restrictions.
    """,
    'author': 'Youssef',
    'website': '',
    'category': 'Tools',
    'depends': ['mail'],
    'assets': {
        "web.assets_backend": [
            'chatter_restrict_edit_delete/static/src/models/message_action_list_inherit.js',
        ],

    },
    'data': [
        "security/chatter_restrict_edit_delete.xml",
    ],

    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
