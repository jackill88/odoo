from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Standard pattern: module_<module_name> boolean to control installation from settings.
    module_pos_payment_emulator = fields.Boolean(
        string="POS Payment Emulator",
        help="Install the POS Payment Emulator module to use a simulated payment terminal.",
    )

