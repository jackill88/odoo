import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class PricelistImporter:
    """
    Handles product.pricelist.item import.
    """
    _name = 'pricelist.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name='product.pricelist.item',
            external_field='id',
            batch_size=1000
        )

        product_map = self._load_product_map(data)
        pricelist_map = self._load_pricelist_map(data)

        def prepare(item):
            product_id = product_map.get(item.get('product_id'))
            pricelist_id = pricelist_map.get(item.get('pricelist'))

            if not product_id:
                raise ValueError(f"Missing product: {item.get('product_id')}")

            if not pricelist_id:
                raise ValueError(f"Missing pricelist: {item.get('pricelist')}")

            return {
                'product_id': product_id,
                'pricelist_id': pricelist_id,
                'applied_on': '0_product_variant',
                'compute_price': 'fixed',
                'fixed_price': item.get('price', 0.0),
                'min_quantity': item.get('min_qty', 1),
                'date_start': item.get('date_start'),
                'date_end': item.get('date_end'),
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
            ('model', '=', 'product.product')
        ])

        return {m.external_id: m.res_id for m in mappings}

    def _load_pricelist_map(self, data):
        names = {r.get('pricelist') for r in data if r.get('pricelist')}

        pricelists = self.env['product.pricelist'].search([
            ('name', 'in', list(names))
        ])

        return {pl.name: pl.id for pl in pricelists}