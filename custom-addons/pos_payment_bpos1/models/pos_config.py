# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    bpos1_merchant_idx = fields.Integer(
        string='BPOS1 Merchant Index',
        help='Optional merchant index sent to the payment terminal as merchant_idx.',
    )

    def _load_pos_self_data_fields(self, config):
        fields_list = super()._load_pos_self_data_fields(config)
        if 'bpos1_merchant_idx' not in fields_list:
            fields_list.append('bpos1_merchant_idx')
        return fields_list
