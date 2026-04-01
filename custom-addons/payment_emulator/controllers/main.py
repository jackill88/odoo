# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http


class PaymentEmulatorController(http.Controller):
    _simulate_url = '/payment/emulator/simulate'

    @http.route(_simulate_url, type='jsonrpc', auth='public')
    def emulator_simulate(self, **data):
        """Simulate payment response (always success)."""
        return http.request.env['payment.transaction'].sudo()._process('emulator', data)
