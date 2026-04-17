# models/external_id_map.py

from odoo import models, fields


class ExternalIdMap(models.Model):
    _name = 'external.id.map'

    external_id = fields.Char(required=True, index=True)
    model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True)

    _sql_constraints = [
        ('uniq_ext_model', 'unique(external_id, model)', 'External ID must be unique per model')
    ]