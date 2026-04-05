# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    weighted_goods_barcode_prefix = fields.Integer(
        string="Weighted goods barcode prefix",
        help="Prefix used for weighted goods barcodes (usually the first two EAN-13 digits).",
        default=20,
    )

    _sql_constraints = [
        (
            "pos_config_weighted_prefix_positive",
            "CHECK(weighted_goods_barcode_prefix >= 0)",
            "The weighted barcode prefix must be positive or zero.",
        ),
    ]

    @api.constrains("weighted_goods_barcode_prefix")
    def _check_weighted_goods_barcode_prefix(self):
        for config in self:
            prefix = config.weighted_goods_barcode_prefix
            if prefix < 0:
                raise ValidationError(
                    _(
                        "Weighted goods barcode prefix must be greater than or equal to 0."
                    )
                )
            if prefix > 99:
                raise ValidationError(
                    _(
                        "Weighted goods barcode prefix must fit on two digits (0-99)."
                    )
                )
