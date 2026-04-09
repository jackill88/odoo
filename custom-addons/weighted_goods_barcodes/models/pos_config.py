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

    weighted_goods_filter_id = fields.Many2one(
        "weighted.goods.filter",
        string="Weighted goods filter",
        domain=[("active", "=", True)],
        help="Select the filter that determines which products are pushed to the scales service.",
        ondelete="set null",
    )

    digital_scales_service_ip_address = fields.Char(
        string="Digital scales service IP address",
        help="IP address or hostname of the HTTP endpoint that receives weighted goods data.",
    )
    digital_scales_service_port = fields.Integer(
        string="Digital scales service port",
        default=80,
        help="Port exposed by the digital scales service; typically 80 or 443.",
    )
    digital_scales_service_api_key = fields.Char(
        string="Digital scales service API key",
        copy=False,
        help="Shared key sent in every request so the digital scales service can authenticate this PoS.",
    )

    _constraint_weighted_prefix_positive = models.Constraint(
        "CHECK(weighted_goods_barcode_prefix >= 0)",
        "The weighted barcode prefix must be positive or zero.",
    )

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

    @api.constrains("digital_scales_service_port")
    def _check_digital_scales_service_port(self):
        for config in self:
            port = config.digital_scales_service_port
            if port and not (1 <= port <= 65535):
                raise ValidationError(
                    _(
                        "Digital scales service port must be between 1 and 65535."
                    )
                )
