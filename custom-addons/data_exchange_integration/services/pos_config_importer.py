# services/pos_config_importer.py
""" loads pos.config data"""

import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class PosConfigImporter:
    """
    Handles product.product import from external system.
    """
    MODEL_NAME = 'pos.config'

    _name = 'pos.config.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name=self.MODEL_NAME,
            external_field='id',
            batch_size=20,
            specific_model_create_method = 'create' # shouldn't just use ORM's 'write' in this case
        )

        pos_payment_methods_map = self._load_pos_payment_methods_category_map(data)

        def prepare(item):
            try:
                ret_item = {
                    'id': item['id'],
                    'name': item['name'],
                }
                if item.get('iface_tax_included'):
                    ret_item.update({'iface_tax_included': item.get('iface_tax_included')})    

                if item.get('picking_policy'):
                    ret_item.update({'picking_policy': item.get('picking_policy')})

                if item.get('payment_method_ids'):
                    _paym_method_ids = []
                    for ext_payment_method_id in self._ensure_list(item.get('payment_method_ids')):
                        _internal_pos_payment_method_id = pos_payment_methods_map.get(str(ext_payment_method_id))

                        if not _internal_pos_payment_method_id:
                            raise ValueError(f"Missing POS payment method ID: ext.id {_internal_pos_payment_method_id}")
                        
                        _paym_method_ids.append(_internal_pos_payment_method_id)

                    ret_item.update({'payment_method_ids': [(6, 0, _paym_method_ids)]})  # replace all

                return ret_item
            except Exception as e:
                _msg = "Bad POS config data: %s", str(e)
                _logger.warning(_msg)

                if job:
                    job.add_log(_msg)
                    job.state = "discarded"

        service.run(data, prepare, job=job)


    def _ensure_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


    def _load_pos_payment_methods_category_map(self, data):
        ext_ids = set()
        for r in data:
            if r.get('payment_method_ids'):
                for ext_categ_id in self._ensure_list(r.get('payment_method_ids')):
                    ext_ids.add(ext_categ_id)

        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', '=', 'pos.payment.method')
        ])

        return {m.external_id: m.res_id for m in mappings}