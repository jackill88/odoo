{
    'name': 'POS Payment BPOS1 Terminal Extension',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Adds the BPOS1-compatible terminal field set and a stubbed success flow for testing.',
    'depends': ['point_of_sale', 'pos_fiscal_integration', 'pos_self_order'],
    'data': [
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_payment_bpos1_terminal/static/src/app/utils/payment/payment_bpos1_terminal.js',
            'pos_payment_bpos1_terminal/static/src/overrides/models/pos_payment.js',
            'pos_payment_bpos1_terminal/static/src/app/components/bpos1_terminal_panel/bpos1_terminal_panel.js',
            'pos_payment_bpos1_terminal/static/src/app/components/bpos1_terminal_panel/bpos1_terminal_panel.xml',
            'pos_payment_bpos1_terminal/static/src/app/screens/payment_screen/payment_screen_patch.js',
            'pos_payment_bpos1_terminal/static/src/app/screens/payment_screen/payment_screen_patch.xml',
        ],
        'pos_self_order.assets': [
            'pos_payment_bpos1_terminal/static/src/app/services/self_order_service_patch.js',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'author': 'Yaroslav Tkachenko',
}
