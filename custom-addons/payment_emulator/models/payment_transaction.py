# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _send_payment_request(self):
        if self.provider_code != 'emulator':
            return super()._send_payment_request()
        payment_data = {
            'reference': self.reference,
            'simulated_state': 'done',
        }
        self._process('emulator', payment_data)

    def _send_capture_request(self):
        if self.provider_code != 'emulator':
            return super()._send_capture_request()
        payment_data = {
            'reference': self.reference,
            'simulated_state': 'done',
            'manual_capture': True,
        }
        self._process('emulator', payment_data)

    def _send_void_request(self):
        if self.provider_code != 'emulator':
            return super()._send_void_request()
        payment_data = {'reference': self.reference, 'simulated_state': 'cancel'}
        self._process('emulator', payment_data)

    def _send_refund_request(self):
        if self.provider_code != 'emulator':
            return super()._send_refund_request()
        payment_data = {'reference': self.reference, 'simulated_state': 'done'}
        self._process('emulator', payment_data)

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'emulator':
            return super()._extract_amount_data(payment_data)
        return None

    def _apply_updates(self, payment_data):
        if self.provider_code != 'emulator':
            return super()._apply_updates(payment_data)

        self.provider_reference = f'emulator-{self.reference}'

        state = payment_data.get('simulated_state', 'done')
        if state == 'pending':
            self._set_pending()
        elif state == 'done':
            if self.capture_manually and not payment_data.get('manual_capture'):
                self._set_authorized()
            else:
                self._set_done()
                if self.operation == 'refund':
                    self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif state == 'cancel':
            self._set_canceled()
        else:
            self._set_error(_("Emulator simulated error."))
