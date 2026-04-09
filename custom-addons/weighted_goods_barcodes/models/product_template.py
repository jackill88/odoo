# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_weighted_bc = fields.Boolean(
        string='Weighted goods barcode',
        help='Check this box when the product is sold through a weighed barcode (PLU + weight).',
        default=False,
    )
    weighted_bc_pos_plu_ids = fields.One2many(
        'product.pos.plu',
        'product_template_id',
        string='Point of Sale PLUs',
    )

    @api.constrains('is_weighted_bc')
    def _check_weighted_bc_fields(self):
        for template in self:
            if template.is_weighted_bc:
                if not template.weighted_bc_pos_plu_ids:
                    raise ValidationError(
                        _('At least one PLU must be defined for weighted products.')
                    )
            elif template.weighted_bc_pos_plu_ids:
                raise ValidationError(
                    _('Uncheck the weighted barcode option before assigning POS PLUs.')
                )

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        return fields + ['is_weighted_bc', 'weighted_bc_pos_plu_ids']
