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
    weighted_bc_plu = fields.Integer(
        string='Weighted goods PLU',
        help='PLU value used in the weighted barcode (0-99999).',
        copy=False,
    )

    _sql_constraints = [
        ('weighted_bc_plu_unique', 'unique(weighted_bc_plu)',
         'Each weighted goods PLU must be unique.'),
    ]

    @api.constrains('is_weighted_bc', 'weighted_bc_plu')
    def _check_weighted_bc_fields(self):
        for template in self:
            if template.is_weighted_bc:
                if template.weighted_bc_plu in (False, None):
                    raise ValidationError(
                        _('A PLU code is required when the product is flagged as weighted.')
                    )
                if not 0 <= template.weighted_bc_plu <= 99999:
                    raise ValidationError(
                        _('The weighted PLU must be between 0 and 99999.')
                    )
            elif template.weighted_bc_plu:
                raise ValidationError(
                    _('Uncheck the weighted barcode option before modifying the PLU.')
                )

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        return fields + ['is_weighted_bc', 'weighted_bc_plu']
