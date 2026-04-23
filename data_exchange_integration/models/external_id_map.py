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
    
    # DB index
    _index = [
        ('model_res_id_idx', 'btree(model, res_id)')
    ]

class Base(models.AbstractModel):
    """handles removal of data in odoo - mapping records will be removed too"""
    _inherit = 'base'

    def unlink(self):
        model = self._name
        if not model == 'external.id.map':

            ids = self.ids

            # delete mappings first
            self.env['external.id.map'].search([
                ('model', '=', model),
                ('res_id', 'in', ids)
            ]).unlink()

        return super().unlink()