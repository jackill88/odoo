import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class GoodsImporter:
    """
    Handles product.product import from external system.
    """
    _name = 'goods.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name='product.product',
            external_field='id',
            batch_size=1000
        )

        def prepare(item):
            try:
                return {
                    'id': item['id'],
                    'name': item['name'],
                    'default_code': item.get('code'),
                    'list_price': item.get('price', 0.0),
                    'active': item.get('active'),
                }
            except Exception as e:
                _msg = "Bad product data: %s", str(e)
                _logger.warning(_msg)

                if job:
                    job.add_log(_msg)

                raise

        service.run(data, prepare, job=job)