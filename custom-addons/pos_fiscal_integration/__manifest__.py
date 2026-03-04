{
    'name': 'POS Fiscal Integration',
    'version': '1.0',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_fiscal_integration/static/src/js/pos_opening_control_patch.js',
            'pos_fiscal_integration/static/src/js/pos_closing_control_patch.js',
            'pos_fiscal_integration/static/src/js/pos_order_payment_validation_patch.js',
            'pos_fiscal_integration/static/src/js/pos_cash_move_patch.js',
            'pos_fiscal_integration/static/src/js/pos_additional_fiscal_screen_button.js',
            'pos_fiscal_integration/static/src/js/pos_additional_fiscal_screen.js',
            'pos_fiscal_integration/static/src/xml/pos_additional_fiscal_screen_button.xml',
            'pos_fiscal_integration/static/src/xml/pos_additional_fiscal_screen.xml',
        ],
    },
    'data': [
        'views/pos_fiscal_integration_view.xml',
    ],
    'installable': True,
}