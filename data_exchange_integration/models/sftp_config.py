# models/sftp_config.py

from odoo import models, fields

class DataImportSftpConfig(models.Model):
    _name = 'data.import.sftp.config'

    name = fields.Char()
    key = fields.Char(index=True)

    host = fields.Char(required=True)
    port = fields.Integer(default=22)
    username = fields.Char(required=True)
    password = fields.Char(required=True)