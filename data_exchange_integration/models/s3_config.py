# models/s3_config.py

from odoo import models, fields

class DataImportS3Config(models.Model):
    _name = 'data.import.s3.config'

    name = fields.Char()
    key = fields.Char(index=True)

    endpoint = fields.Char(required=True)  # http://host:9000
    access_key = fields.Char(required=True)
    secret_key = fields.Char(required=True)