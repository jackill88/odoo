# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class WeightedGoodsFilter(models.Model):
    _name = "weighted.goods.filter"
    _description = "Filter for weighted goods exported to the scales service"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    product_category_id = fields.Many2one(
        "product.category",
        string="Product Category",
        help="Limit the export to the selected category and its children.",
    )
    product_attribute_value_ids = fields.Many2many(
        "product.template.attribute.value",
        string="Variant Values",
        help="Filter products that have at least one of these attribute values.",
    )
    additional_product_template_ids = fields.Many2many(
        "product.template",
        string="Additional static products",
        help="Always include these products in the export, regardless of the other criteria.",
    )
    only_weighted_goods = fields.Boolean(
        string="Only weighted goods",
        default=True,
        help="Restrict the export to products that are explicitly flagged as weighted.",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Filtered products",
    )

    pos_config_ids = fields.One2many(
        "pos.config",
        "weighted_goods_filter_id",
        string="Point of Sale configurations",
    )

    def _build_product_domain(self):
        domain = []
        if self.product_category_id:
            domain.append(("categ_id", "child_of", self.product_category_id.id))
        if self.product_attribute_value_ids:
            domain.append((
                "product_template_attribute_value_ids",
                "in",
                self.product_attribute_value_ids.ids,
            ))
        if self.only_weighted_goods:
            domain.append(("is_weighted_bc", "=", True))
        return domain

    def get_products(self):
        """Return the product variants that match this filter."""
        self.ensure_one()
        domain = self._build_product_domain()
        products = self.env["product.product"].search(domain) if domain else self.env["product.product"].browse()
        if self.additional_product_template_ids:
            products |= self.additional_product_template_ids.mapped("product_variant_ids")
        return products

    @api.depends(
        "product_category_id",
        "product_attribute_value_ids",
        "additional_product_template_ids",
        "only_weighted_goods",
    )
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.get_products())
