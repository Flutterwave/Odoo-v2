# -*- coding: utf-8 -*-
{
    'name': 'Flutterwave for Business',
    'version': '3.0',
    'category': 'eCommerce',
    'sequence': -100,
    'summary': 'The Official Flutterwave Payment Acquirer for Odoo Clients',
    'author': 'Flutterwave Developers',
    'website': 'https://app.flutterwave.com/',
    'description': """Flutterwave Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_rave_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'unistall_hook': 'uninstall_hook',
    'license': 'LGPL-3',    
}
