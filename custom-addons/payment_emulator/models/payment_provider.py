# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from odoo.addons.payment_emulator import const


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('emulator', 'Emulator')],
        ondelete={'emulator': 'set default'},
    )

    def _compute_feature_support_fields(self):
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'emulator').update({
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
            'support_tokenization': False,
        })

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code != 'emulator':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES
