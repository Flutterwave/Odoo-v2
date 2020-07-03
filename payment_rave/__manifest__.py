# -*- coding: utf-8 -*-
{
    'name': 'Rave Payment Acquirer',
    'category': 'eCommerce',
    'summary': 'Payment Acquirer: Rave Implementation',
    'version': '2',
    'license': 'AGPL-3',
    'author': 'Flutterwave Technology Solutions',
    'website': 'https://rave.flutterwave.com/',
    'description': """Flutterwave Rave Payment Acquirer""",
    'depends': ['payment','website'],
    'data': [
        'views/payment_views.xml',
        'views/payment_rave_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook'
    
}
