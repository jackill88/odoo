{
    'name': 'POS Payment Emulator',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Simulated POS payment terminal for testing and demos',
    'depends': ['point_of_sale', 'pos_self_order', 'pos_self_order_terminal_registry'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_payment_emulator/static/src/app/utils/payment/payment_emulator.js',
        ],
        'web.assets_backend': [
            'pos_payment_emulator/static/src/backend/**/*',
        ],
        # Load the kiosk/self-order overrides in the self-order frontend app
        'pos_self_order.assets': [
            'pos_payment_emulator/static/src/app/overrides/self_order_service_patch.js',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
