# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    _DEFAULT_SCALES_PATH = "/digital-scales/upload"

    pos_weighted_goods_barcode_prefix = fields.Integer(
        string="Weighted barcode prefix",
        related="pos_config_id.weighted_goods_barcode_prefix",
        readonly=False,
        help="Define the prefix used by weighted goods barcodes for the selected PoS.",
    )
    pos_weighted_goods_filter_id = fields.Many2one(
        "weighted.goods.filter",
        string="Weighted goods filter",
        related="pos_config_id.weighted_goods_filter_id",
        readonly=False,
        help="Select which filter defines the products that are exported to the scales service.",
    )
    pos_digital_scales_service_ip_address = fields.Char(
        string="Digital scales service IP address",
        related="pos_config_id.digital_scales_service_ip_address",
        readonly=False,
        help="IP address or hostname that receives the weighted goods from this PoS.",
    )
    pos_digital_scales_service_port = fields.Integer(
        string="Digital scales service port",
        related="pos_config_id.digital_scales_service_port",
        readonly=False,
        help="Port exposed by the digital scales service for HTTP requests.",
    )
    pos_digital_scales_service_api_key = fields.Char(
        string="Digital scales service API key",
        related="pos_config_id.digital_scales_service_api_key",
        readonly=False,
        help="API key that will be sent with each request so the scales endpoint can authenticate.",
    )

    def action_upload_weighted_goods_to_scales(self):
        """Return the payload and endpoint info so the JS can upload it."""
        self.ensure_one()
        config = self.pos_config_id
        if not config:
            raise UserError(_("Select the Point of Sale before uploading PLUs."))
        filter_record = config.weighted_goods_filter_id
        if not filter_record:
            raise UserError(
                _("Specify a weighted goods filter on the PoS tab before uploading PLUs.")
            )

        payload = self._build_scales_payload(filter_record.get_products(), config)
        if not payload["items"]:
            raise UserError(
                _("No weighted goods PLUs are defined for the selected filter/PoS.")
            )

        url = self._build_scales_url(config)
        headers = {"Content-Type": "application/json"}
        if config.digital_scales_service_api_key:
            headers["x-api-key"] = config.digital_scales_service_api_key

        return {
            "type": "ir.actions.client",
            "tag": "digital_scales_upload",
            "params": {
                "url": url,
                "headers": headers,
                "payload": payload,
            },
        }

    def _build_scales_payload(self, products, config):
        seen_tmpl = set()
        items = []
        for product in products:
            template = product.product_tmpl_id
            if template.id in seen_tmpl:
                continue
            seen_tmpl.add(template.id)

            plu_record = template.weighted_bc_pos_plu_ids.filtered(
                lambda rec: rec.pos_config_id == config
            )[:1]
            if not plu_record:
                _logger.warning(
                    "Skipping %s, no PLU defined for PoS %s",
                    template.display_name,
                    config.display_name,
                )
                continue

            plu_value = plu_record.plu
            items.append(
                {
                    "plu": plu_value,
                    "name": template.name,
                    "price": template.list_price,
                    "code": str(plu_value),
                    "full_name": template.display_name,
                    "goods_type": 0,
                }
            )
        return {"items": items, "partial": False}

    def _build_scales_url(self, config):
        ip = (config.digital_scales_service_ip_address or "").strip()
        port = config.digital_scales_service_port
        if not ip or not port:
            raise UserError(
                _("Digital scales service IP address and port must be configured.")
            )
        host = ip.replace("http://", "").replace("https://", "").rstrip("/")
        scheme = "https" if port == 443 else "http"
        return f"{scheme}://{host}:{port}{self._DEFAULT_SCALES_PATH}"
