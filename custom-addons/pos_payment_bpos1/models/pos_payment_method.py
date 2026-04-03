# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.fields import Domain


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('bpos1', 'BPOS1 Terminal')]

    @api.model
    def _load_pos_self_data_domain(self, data, config):
        domain = super()._load_pos_self_data_domain(data, config)
        if config.self_ordering_mode == 'kiosk':
            domain = Domain.OR([
                [('use_payment_terminal', '=', 'bpos1'), ('id', 'in', config.payment_method_ids.ids)],
                domain,
            ])
        return domain

    def _payment_request_from_kiosk(self, order):
        if self.use_payment_terminal != 'bpos1':
            return super()._payment_request_from_kiosk(order)
        return 'Success'
