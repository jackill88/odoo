{
    "name": "YASK Weighted Goods Barcodes",
    "version": "1.0",
    'sequence': 400,
    "category": "Point of Sale",
    "summary": "Support scanning weighted EAN-13 barcodes with PLU + weight information.",
    "depends": ["sale", "point_of_sale"],
    "data": [
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "weighted_goods_barcodes/static/src/app/services/barcode_reader_patch.js",
            "weighted_goods_barcodes/static/src/app/services/pos_store_patch.js",
            "weighted_goods_barcodes/static/src/app/services/weighted_goods_barcode_service.js",
        ]
    },
    "installable": True,
    "license": "LGPL-3",
    "author": "Yaroslav Tkachenko"
}
