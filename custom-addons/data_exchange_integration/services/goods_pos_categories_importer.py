import logging

from datetime import datetime
from typing import List
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class ProductPosCategoryImporter:
    """
    Handles pos_categ_ids for product.template.
    Doesn't create any new data - just connects categories with products
    """
    _name = 'pricelist.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data:List[dict], job=None):
        service = ImporterService(
            self.env,
            model_name='product.template',
            external_field='product_id',
            batch_size=1000
        )

        product_map = self._load_product_map(data)
        pos_categories_map = self._load_pos_category_map(data)
       

        _today = datetime.now().date()

        def prepare(item):
            product_ext_id = item.get('product_id')
            pos_category_external_ids = self._ensure_list(item.get('pos_categ_ids'))

            product_id = product_map.get(str(product_ext_id))

            categ_ids = []
            if pos_category_external_ids:
                for ext_categ_id in pos_category_external_ids:
                    _internal_pos_categ_id = pos_categories_map.get(str(ext_categ_id))

                    if not _internal_pos_categ_id:
                        raise ValueError(f"Missing POS category ID: ext.id {_internal_pos_categ_id}")
                    
                    categ_ids.append(_internal_pos_categ_id)


            if not product_id:
                raise ValueError(f"Missing product: {product_ext_id}")

            return {
                'id': product_id,
                'pos_categ_ids': [(6, 0, categ_ids)], # replace all
            }

        service.run(data, prepare, job=job)

    # -----------------------------
    # PRELOAD HELPERS
    # -----------------------------

    def _load_product_map(self, data):
        ext_ids = {r.get('product_id') for r in data if r.get('product_id')}

        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', '=', 'product.template')
        ])

        return {m.external_id: m.res_id for m in mappings}
    
    def _ensure_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _load_pos_category_map(self, data):
        ext_ids = set()
        for r in data:
            if r.get('pos_categ_ids'):
                for ext_categ_id in self._ensure_list(r.get('pos_categ_ids')):
                    ext_ids.add(ext_categ_id)

        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', '=', 'pos.category')
        ])

        return {m.external_id: m.res_id for m in mappings}