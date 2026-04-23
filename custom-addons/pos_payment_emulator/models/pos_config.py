from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _supported_kiosk_payment_terminal(self):
        """Allow the emulator to be used as a kiosk payment terminal."""
        terminals = super()._supported_kiosk_payment_terminal()
        if 'emulator' not in terminals:
            terminals.append('emulator')
        return terminals
    
    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        fields = res['search_params']['fields']
        if 'self_ordering_mode' not in fields:
            fields.append('self_ordering_mode')
        return res

