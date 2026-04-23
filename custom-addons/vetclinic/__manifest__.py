# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vetclinic module',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': 250,
    'summary': 'Adds extra models for veterinary clinic (animals, veterinarians, examinations etc...)',
    'depends': ['product', 'purchase', 'sale', 'point_of_sale', 'pos_self_order'],
    'data': [
        'security/ir.model.access.csv',
        'views/vetclinic_views.xml',
        'views/menu.xml',
        'views/sales_order_extended_view.xml',
    ],
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
    # 'assets': {
    #     'web.assets_frontend': [
    #         'payment_emulator/static/src/interactions/**/*',
    #     ],
    # },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'author': 'Yaroslav Tkachenko'
}
