{
    'name': "Extra barcodes for product template",
    'summary': "Adds a possibility to store more than 1 barcode per product template",
    'description': "Adds a possibility to store more than 1 barcode per product template",
    'author': "Yaroslav Tkachenko",
    'category': 'Sales',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ["sale", "point_of_sale", "pos_self_order"],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/product_template_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'product_extra_barcodes/static/src/app/utils/extra_barcode_utils.js',
            'product_extra_barcodes/static/src/app/models/product_extra_barcodes.js',
            'product_extra_barcodes/static/src/app/screens/product_screen_patch.js',
        ],
        'pos_self_order.assets': [
            'product_extra_barcodes/static/src/app/services/self_order_extra_barcode.js',
        ],
    },
    "installable": True,
    "license": "LGPL-3",
}
