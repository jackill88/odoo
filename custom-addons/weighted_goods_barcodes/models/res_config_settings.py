# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_weighted_goods_barcode_prefix = fields.Integer(
        string="Weighted barcode prefix",
        related="pos_config_id.weighted_goods_barcode_prefix",
        readonly=False,
        help="Define the prefix used by weighted goods barcodes for the selected PoS.",
    )
    pos_weighted_goods_filter_id = fields.Many2one(
        "weighted.goods.filter",
        string="Weighted goods filter",
        related="pos_config_id.weighted_goods_filter_id",
        readonly=False,
        help="Select which filter defines the products that are exported to the scales service.",
    )
