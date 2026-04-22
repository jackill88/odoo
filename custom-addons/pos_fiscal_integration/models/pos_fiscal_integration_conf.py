import logging
from odoo import fields, models
from odoo import api
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
    
    # @api.model
    # def _load_pos_self_data_read(self, records, config):
    #     read_records = super()._load_pos_data_read(records, config)
    #     if not read_records:
    #         return read_records
    #     # record = read_records[0]
    #     # record["use_pos_fiscal_service"]= config.use_pos_fiscal_service
    #     # record["fiscal_service_ip"]= config.fiscal_service_ip
    #     # record["fiscal_service_port"]= config.fiscal_service_port
    #     # record["pos_fiscal_service_api_key"]=  config.pos_fiscal_service_api_key
    #     return read_records
        

    # def _load_pos_self_data_fields(self, config):
    #     fields_list = super()._load_pos_self_data_fields(config)
    #     for field_name in (
    #         'use_pos_fiscal_service',
    #         'fiscal_service_ip',
    #         'fiscal_service_port',
    #         'pos_fiscal_service_api_key'
    #     ):
    #         if field_name not in fields_list:
    #             fields_list.append(field_name)
    #     return fields_list

    # def load_data_params(self):
    #     response = super().load_data_params()

    #     if 'pos.config' in response:
    #         if 'relations' in response['pos.config']:
    #             for field_name, field_value in {
    #                 'use_pos_fiscal_service': {'name': 'use_pos_fiscal_service', 'type': 'boolean', 'compute': False, 'related': False},
    #                 'fiscal_service_ip':{'name': 'fiscal_service_ip', 'type': 'char', 'compute': False, 'related': False},
    #                 'fiscal_service_port':{'name': 'fiscal_service_port', 'type': 'integer', 'compute': False, 'related': False},
    #                 'pos_fiscal_service_api_key':{'name': 'pos_fiscal_service_api_key', 'type': 'char', 'compute': False, 'related': False}
    #                 }.items():
    #                 if field_name not in response['pos.config']['relations']:
    #                     response['pos.config']['relations'].append(field_name)      

    #     return response