# -*- coding: utf-8 -*-
{
    "name": "POS Self Service Product Search",
    "version": "1.0",
    "summary": "Adds a product search bar to the POS Self Order interface.",
    "category": "Point Of Sale",
    "depends": ["pos_self_order"],
    "data": [],
    "assets": {
        "pos_self_order.assets": [
            "pos_self_service_product_search/static/src/app/catalog_navigation/catalog_navigation_patch.js",
            "pos_self_service_product_search/static/src/app/product_search/product_list_page_search.js",
            "pos_self_service_product_search/static/src/app/product_search/product_list_page_search.xml",
            "pos_self_service_product_search/static/src/app/styles/product_search.scss"
        ]
    },
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3"
}
