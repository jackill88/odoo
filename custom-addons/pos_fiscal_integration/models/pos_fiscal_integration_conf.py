import logging
from odoo import fields, models
_logger = logging.getLogger(__name__)


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

    def _load_pos_self_data_read(self, records, config):
        result = super()._load_pos_self_data_read(records, config)

        if not result:
            return result

        record = result[0]

        # 🔥 FORCE your fields into final payload
        record.update({
            "use_pos_fiscal_service": config.use_pos_fiscal_service,
            "fiscal_service_ip": config.fiscal_service_ip,
            "fiscal_service_port": config.fiscal_service_port,
            "pos_fiscal_service_api_key": config.pos_fiscal_service_api_key
        })

        return result
        

    def _load_pos_self_data_fields(self, config):
        fields_list = super()._load_pos_self_data_fields(config)
        for field_name in (
            'use_pos_fiscal_service',
            'fiscal_service_ip',
            'fiscal_service_port',
            'pos_fiscal_service_api_key'
        ):
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list