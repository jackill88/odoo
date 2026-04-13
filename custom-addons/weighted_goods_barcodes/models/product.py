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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_weighted_bc = fields.Boolean()
    weighted_bc_plu_for_pos = fields.Char()

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        return fields + ['is_weighted_bc', 'weighted_bc_plu_for_pos']


    def _load_extra_weighted_barcode_data(self, records, read_records, config):
        # 1 Get templates
        templates = records.mapped('product_tmpl_id')

        # 2 Map template → is_weighted_bc
        is_weighted_map = {
            tmpl.id: tmpl.is_weighted_bc
            for tmpl in templates
        }

        # 3 Fetch PLUs
        plu_records = self.env['product.pos.plu'].search([
            ('product_template_id', 'in', templates.ids),
            ('pos_config_id', '=', config.id),
            ('active', '=', True),
        ])

        # 4 Map template → PLU
        plu_map = {
            plu.product_template_id.id: plu.plu
            for plu in plu_records
        }

        # 5 Inject into product.product data
        for record in read_records:
            tmpl_ids = record['product_tmpl_id']  # [id, name]
            if isinstance(tmpl_ids, list):
               tmpl_id = tmpl_ids[0]
            else:
               tmpl_id = tmpl_ids

            record['is_weighted_bc'] = is_weighted_map.get(tmpl_id, False)
            record['weighted_bc_plu_for_pos'] = plu_map.get(tmpl_id, False)

        return read_records or []


    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)

        if not records or not config:
            return read_records

        return self._load_extra_weighted_barcode_data(records, read_records, config)
    

    def _weighted_goods_barcodes_extra_fields(self):
        return ['is_weighted_bc', 'weighted_bc_plu_for_pos']
    

    @api.model
    def _load_pos_self_data_fields(self, config):
        fields = super()._load_pos_self_data_fields(config)
        return fields + self._weighted_goods_barcodes_extra_fields()
    

    def _load_pos_self_data_read(self, records, config):
        read_records = super()._load_pos_self_data_read(records, config)

        if not records or not config:
            return read_records

        return self._load_extra_weighted_barcode_data(records, read_records, config)
        