# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Emulator (mock provider)',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'Emulator payment provider for testing (e.g. Kiosk / website checkout).',
    'depends': ['payment'],
    'data': [
        'views/payment_emulator_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'payment_emulator/static/src/interactions/**/*',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'author': 'Yaroslav Tkachenko'
}
