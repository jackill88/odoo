# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_pos_payment_bpos1 = fields.Boolean(
        string="POS Payment BPOS1",
        help="Install the BPOS1 payment method helper module to expose the terminal integration in the POS settings.",
    )
