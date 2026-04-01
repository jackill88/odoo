{
    'name': 'POS Payment BPOS1',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Connect Point of Sale to a BPOS1 terminal via the fiscal layer endpoints.',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_payment_bpos1/static/src/app/utils/payment/payment_bpos1.js',
            'pos_payment_bpos1/static/src/app/services/pos_store.js',
            'pos_payment_bpos1/static/src/overrides/models/pos_payment.js',
        ],
        'web.assets_backend': [
            'pos_payment_bpos1/static/src/backend/pos_payment_provider_cards/pos_payment_provider_cards.js',
            'pos_payment_bpos1/static/src/backend/pos_payment_provider_cards/pos_payment_provider_cards.xml',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'author': 'Yaroslav Tkachenko'
}
