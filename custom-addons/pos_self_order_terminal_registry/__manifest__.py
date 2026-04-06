{
    'name': 'POS Self Order Terminal Registry',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Shared registry for adding terminal payment methods to the self-order flow.',
    'depends': ['point_of_sale', 'pos_self_order'],
    'assets': {
        'pos_self_order.assets': [
            'pos_self_order_terminal_registry/static/src/app/services/self_order_terminal_registry.js',
            'pos_self_order_terminal_registry/static/src/app/overrides/self_order_service_filter_patch.js',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
