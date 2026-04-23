import json

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_extra_barcode_ids = fields.One2many(
        "product.extra.barcode",
        "product_template_id",
        string="Extra barcodes",
    )
    extra_barcode_values = fields.Text(
        string="Extra barcode values",
        compute="_compute_extra_barcode_values",
        help="JSON array of active extra barcodes for this template.",
    )

    @api.depends(
        "product_extra_barcode_ids.extra_barcode",
        "product_extra_barcode_ids.is_active",
    )
    def _compute_extra_barcode_values(self):
        for template in self:
            values = (
                template.product_extra_barcode_ids.filtered("is_active")
                .mapped("extra_barcode")
            )
            template.extra_barcode_values = json.dumps(values or [])


class ProductProduct(models.Model):
    _inherit = "product.product"

    extra_barcode_values = fields.Text(
        related="product_tmpl_id.extra_barcode_values",
        string="Extra barcode values",
        readonly=True,
    )

    @api.model
    def _load_pos_data_fields(self, config):
        params = super()._load_pos_data_fields(config)
        if "extra_barcode_values" not in params:
            params = params + ["extra_barcode_values"]
        return params
