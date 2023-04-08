# -*- coding: utf-8 -*-

{
    'name': 'Flutterwave for Business',
    'category': 'eCommerce',
    'summary': 'The Official Odoo Module for F4B Commerce',
    'version': '1',
    'license': 'AGPL-3',
    'author': 'Flutterwave Technology Solutions',
    'website': 'https://rave.flutterwave.com/',
    'description': """The Official Odoo Module for F4B Commerce""",
    'depends': ['payment','website'],
    'data': [
        'views/payment_views.xml',
        'views/payment_rave_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
