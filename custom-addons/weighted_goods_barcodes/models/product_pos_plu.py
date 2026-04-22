# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductPosPlu(models.Model):
    _name = "product.pos.plu"
    _description = "Product PLU assigned to a Point of Sale"
    _order = "pos_config_id, product_template_id"

    product_template_id = fields.Many2one(
        "product.template",
        string="Product Template",
        required=True,
        ondelete="cascade",
    )
    pos_config_id = fields.Many2one(
        "pos.config",
        string="Point of Sale",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="pos_config_id.company_id",
        readonly=True,
        store=True,
        check_company=True,
    )
    plu = fields.Integer(
        string="PLU",
        required=True,
        help="PLU code used for this product on the selected PoS (0-99999).",
    )
    active = fields.Boolean(default=True)

    _constraint_unique_pos_plu = models.Constraint(
        "unique(pos_config_id, plu)",
        _("A PLU code must be unique per Point of Sale."),
    )
    _constraint_unique_product_pos = models.Constraint(
        "unique(product_template_id, pos_config_id)",
        _("Each product can have only one PLU per PoS configuration."),
    )

    @api.constrains("plu")
    def _check_plu_range(self):
        for record in self:
            if not 0 <= record.plu <= 99999:
                raise ValidationError(_("PLU must be between 0 and 99999."))
