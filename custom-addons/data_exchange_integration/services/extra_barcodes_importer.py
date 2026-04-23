import logging

from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class ExtraBarcodesImporter:
    """
    Handles product.extra.barcode import from external system.
    """
    _name = 'goods.extra_barcode.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        records = self._flatten_records(data, job)
        if not records:
            return

        product_template_map = self._load_product_template_map(records)

        service = ImporterService(
            self.env,
            model_name='product.extra.barcode',
            external_field='id',
            batch_size=1000
        )

        def _prepare(item):
            product_ext_id = item.get('product_ext_id')
            template_id = product_template_map.get(product_ext_id)
            item_id = item.get('id')

            if not product_ext_id:
                raise ValueError("Missing product identifier")
            
            if not item_id:
                raise ValueError("Missing barcode item ID")

            if not template_id:
                raise ValueError(f"Unknown product for external id {product_ext_id}")

            barcode = item.get('extra_barcode')
            if not barcode:
                raise ValueError(f"Missing barcode value for {product_ext_id}")

            # fields should match with what is in the model!
            return {
                'product_template_id': template_id,
                'extra_barcode': barcode,
                'is_active': item.get('is_active', True),
            }

        service.run(records, _prepare, job=job)

    # ------------------------------------------------------------------
    def _flatten_records(self, data, job):
        if not isinstance(data, list):
            _msg = f"Extra barcodes payload is not a list ({type(data).__name__})"
            _logger.warning(_msg)
            if job:
                job.add_log(_msg)
                job.state = 'discarded'
            return []

        flattened = []
        seen = set()

        for item in data:
            product_ext_id = item.get('id')
            if not product_ext_id:
                _logger.warning("Skipping extra barcodes entry without product identifier")
                continue

            barcode_inputs = self._ensure_list(item.get('barcodes'))

            if not barcode_inputs:
                continue

            default_active = item.get('is_active', item.get('active', True))

            for raw_barcode in barcode_inputs:
                barcode_value, active_flag = self._normalize_barcode(raw_barcode)
                if not barcode_value:
                    continue

                is_active = active_flag if active_flag is not None else default_active

                ext_id = f"{product_ext_id}:{barcode_value}"
                if ext_id in seen:
                    continue

                seen.add(ext_id)
                flattened.append({
                    'id': ext_id,
                    'product_ext_id': str(product_ext_id),
                    'extra_barcode': barcode_value,
                    'is_active': bool(is_active),
                })

        return flattened

    def _ensure_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _normalize_barcode(self, raw):
        if raw is None:
            return None, None


        value = raw
        active_flag = True # default = True

        if value is None:
            return None, active_flag

        return str(value).strip(), active_flag

    def _load_product_template_map(self, records):
        ext_ids = {rec['product_ext_id'] for rec in records if rec.get('product_ext_id')}
        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', 'in', ['product.template'])
        ])

        template_map = {}

        template_mappings = mappings.filtered(lambda rec: rec.model == 'product.template')
        if template_mappings:
            templates = self.env['product.template'].browse(template_mappings.mapped('res_id'))
            template_dict = {tmpl.id: tmpl.id for tmpl in templates}
            for mapping in template_mappings:
                if mapping.res_id in template_dict:
                    template_map[mapping.external_id] = template_dict[mapping.res_id]


        return template_map
