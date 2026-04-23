# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Pricelist: add last purchase price option',
    'version': '1.0',
    'category': 'Products/Pricelists',
    'sequence': 400,
    'summary': 'Adds extra options to the pricelist item (base price options)',
    'depends': ['product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_item_view.xml',
        'views/purchase_order_price_wizard_view.xml',
        'views/purchase_order_action_to_open_pricelist.xml'
    ],
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
    # 'assets': {
    #     'web.assets_frontend': [
    #         'payment_emulator/static/src/interactions/**/*',
    #     ],
    # },
    'installable': True,
    'license': 'LGPL-3',
}
