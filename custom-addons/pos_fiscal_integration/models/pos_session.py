from odoo import models

class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        res["search_params"]["fields"].extend([
            "pos_fiscal_service_api_key",
            "unique_fiscal_number",
            "fiscal_service_ip",
            "fiscal_service_port",
        ])
        return res