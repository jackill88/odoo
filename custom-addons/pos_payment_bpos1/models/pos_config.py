# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    bpos1_merchant_idx = fields.Integer(
        string='BPOS1 Merchant Index',
        help='Optional merchant index sent to the payment terminal as merchant_idx.',
    )

    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        for field_name in ('currency_id', 'company_id', 'use_pricelist'):
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list

    def _load_pos_self_data_fields(self, config):
        fields_list = super()._load_pos_self_data_fields(config)
        for field_name in (
            'access_token',
            'self_ordering_mode',
            'iface_available_categ_ids',
            'self_ordering_available_language_ids',
            'currency_id',
            'company_id',
            'bpos1_merchant_idx',
        ):
            if field_name not in fields_list:
                fields_list.append(field_name)
        for field_name in ('payment_method_ids', 'self_order_online_payment_method_id'):
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list
    
    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        fields = res['search_params']['fields']
        if 'self_ordering_mode' not in fields:
            fields.append('self_ordering_mode')
        return res
