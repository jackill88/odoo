from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    animal_ids = fields.One2many(
        'animal',
        'customer_id',
        string='Animals'
    )