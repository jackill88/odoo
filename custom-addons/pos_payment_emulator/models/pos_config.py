from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _supported_kiosk_payment_terminal(self):
        """Allow the emulator to be used as a kiosk payment terminal."""
        terminals = super()._supported_kiosk_payment_terminal()
        if 'emulator' not in terminals:
            terminals.append('emulator')
        return terminals

