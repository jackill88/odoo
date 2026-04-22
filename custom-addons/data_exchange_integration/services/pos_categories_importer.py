# services/pos_categories_importer.py
""" loads pos.category data"""

import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class PosCategoriesImporter:
    """
    Handles product.product import from external system.
    """
    _name = 'pos.category.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name='pos.category',
            external_field='id',
            batch_size=1000
        )

        def prepare(item):
            try:
                return {
                    'id': item['id'],
                    'name': item['name'],
                }
            except Exception as e:
                _msg = "Bad POS categoty data: %s", str(e)
                _logger.warning(_msg)

                if job:
                    job.add_log(_msg)
                    job.state = "discarded"

        service.run(data, prepare, job=job)