from odoo import models, fields


class PosConfig(models.Model):
    _inherit = ["pos.config"]

    use_pos_fiscal_service = fields.Boolean(
        string="Use POS Fiscal Service Layer",
        help="Enable direct communication with local fiscal service."
    )

    pos_fiscal_service_api_key = fields.Char(
        string="Fiscal Service API Key",
        size=50,
        help="Fiscal Service API Key."
    )

    unique_fiscal_number = fields.Char(
        string="Unique fiscal ID for the POS",
        size=36,
        help="Unique fiscal ID for the POS."
    )

    fiscal_service_ip = fields.Char(
        string="Fiscal Service IP Address",
        size=30,
        help="Fiscal Service IP Address."
    )

    fiscal_service_port = fields.Integer(
        string="Fiscal Service Port",
        help="Port of the fiscal service (e.g. 8000)."
    )