# -*- coding: utf-8 -*-

{
    'name': 'Rave Payment Acquirer',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: Rave Implementation',
    'version': '1.0',
    'description': """Rave Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_rave_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
