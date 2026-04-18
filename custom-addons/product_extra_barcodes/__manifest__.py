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
    "installable": True,
    "license": "LGPL-3",
}

