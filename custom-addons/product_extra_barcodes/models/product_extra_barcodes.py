# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductExtraBarcode(models.Model):
    _name = "product.extra.barcode"
    _description = "Extra product barcodes"

    product_template_id = fields.Many2one(
        "product.template",
        string="Product Template",
        required=True,
        ondelete="cascade",
    )
    extra_barcode = fields.Char(
        string="extra barcode",
        required=True,
        help="Extra barcode",
    )
    is_active = fields.Boolean(default=True)

    _constraint_unique_extra_barcode_per_product = models.Constraint(
        "unique(product_template_id, extra_barcode)",
        _("An extra barcode should be unique per a product template"),
    )

