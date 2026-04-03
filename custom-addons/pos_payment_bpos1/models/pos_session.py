# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        fields = res['search_params']['fields']
        if 'bpos1_merchant_idx' not in fields:
            fields.append('bpos1_merchant_idx')
        return res
