{
    'name': 'Automatic Payment to Journal Entry Integration',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Automatically generates a linked custom Journal Entry upon payment confirmation.',
    'description': """
Automatic Payment to Journal Entry Integration
==============================================
This module extends the standard payment workflow.
When a payment is confirmed/posted, it automatically creates a Journal Entry (account.move)
using the data from the current payment record (amount, partner, journal, currency, date, memo).
It also adds a smart button on the Payment form to quickly access the generated Journal Entry.
    """,
    'author': 'Your Company',
    'depends': ['account'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
