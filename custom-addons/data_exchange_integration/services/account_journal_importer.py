# services/pos_config_importer.py
""" loads account.journal"""

import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class AccountJournalImporter:
    """
    Handles product.product import from external system.
    """
    MODEL_NAME = 'account.journal'

    _name = 'account.journal.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name=self.MODEL_NAME,
            external_field='id',
            batch_size=20,
            specific_model_create_method = 'create', # shouldn't just use ORM's 'write' in this case
            specific_model_write_method = 'write' # using function from the model
        )

        def prepare(item):
            try:
                ret_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'code': item['code'],
                    'active': True,
                    'type': 'cash',                  
                }

                return ret_item
            except Exception as e:
                _msg = "Bad Account journal data: %s", str(e)
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
