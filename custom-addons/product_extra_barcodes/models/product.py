from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_extra_barcode_ids = fields.One2many(
        'product.extra.barcode',
        'product_template_id',
        string='Extra barcodes',
    )