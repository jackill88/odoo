# services/product_pricelist_type_importer.py
"""handles product.pricelist data"""

import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class ProductPricelistTypeImporter:
    """
    Handles product.pricelist (price type) import from external system.
    """
    _name = 'product.pricelist.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name='product.pricelist',
            external_field='id',
            batch_size=50
        )

        def prepare(item):
            try:
                return {
                    'id': item['id'],
                    'name': item['name'],
                    'active': item.get('active', True),
                }
            except Exception as e:
                _msg = "Bad Pricelist type data: %s", str(e)
                _logger.warning(_msg)

                if job:
                    job.add_log(_msg)
                    job.state = "discarded"

        service.run(data, prepare, job=job)