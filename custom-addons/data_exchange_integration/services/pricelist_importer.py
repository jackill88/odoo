import logging

from datetime import datetime
from typing import List
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class PricelistImporter:
    """
    Handles product.pricelist.item import.
    """
    _name = 'pricelist.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data:List[dict], job=None):
        service = ImporterService(
            self.env,
            model_name='product.pricelist.item',
            external_field='id',
            batch_size=1000
        )

        product_map = self._load_product_map(data)
        pricelist_map = self._load_pricelist_map(data)

        # add synthetic id to the data
        for rec in data:
            rec.update({"id": f"{rec.get('product_id')}:{rec.get('pricelist_id')}"})
        

        _today = datetime.now().date()

        def prepare(item):
            product_ext_id = item.get('product_id')
            pricelist_external_id = item.get('pricelist_id')

            product_id = product_map.get(str(product_ext_id))
            pricelist_id = pricelist_map.get(str(pricelist_external_id))

            if not product_id:
                raise ValueError(f"Missing product: {product_ext_id}")

            if not pricelist_id:
                raise ValueError(f"Missing pricelist: {pricelist_external_id}")

            return {
                'id': item.get('id'),
                'product_id': product_id,
                'pricelist_id': pricelist_id,
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': item.get('price', 0.0),
                'min_quantity': item.get('min_qty', 1),
                'date_start': item.get('date_start', _today),
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

    def _load_pricelist_map(self, data):
        ext_ids = {r.get('pricelist_id') for r in data if r.get('pricelist_id')}

        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', '=', 'product.pricelist')
        ])

        return {m.external_id: m.res_id for m in mappings}