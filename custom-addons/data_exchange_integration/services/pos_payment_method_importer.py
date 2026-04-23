# services/pos_payment_method_importer.py
""" loads pos.payment.method data"""

import logging
from .importer_service import ImporterService

_logger = logging.getLogger(__name__)


class PosPaymentMethodImporter:
    """
    Handles pos.payment.method import from external system.
    """
    MODEL_NAME = 'pos.payment.method'

    _name = 'pos.payment.method.importer'

    def __init__(self, env):
        self.env = env

    def run(self, data, job=None):
        service = ImporterService(
            self.env,
            model_name=self.MODEL_NAME,
            external_field='id',
            batch_size=20,
            specific_model_create_method = 'create', # shouldn't just use ORM's 'write' in this case
            specific_model_write_method = 'write'  # shouldn't just use ORM's 'write' in this case - using model's own method
        )

        _account_journal_map = self._load_account_journal_map(data)


        def prepare(item):

            try:

                _acc_journal_id = _account_journal_map.get(str(item['id']))

                if not _acc_journal_id:
                    raise ValueError(f"Can't find account.journal for external ID {item['id']}")

                ret_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': 'cash',
                    'is_cash_count':True,
                    'journal_id': _acc_journal_id,
                    'active': True, 
                }

                return ret_item
            except Exception as e:
                _msg = "Bad POS payment method data: %s", str(e)
                _logger.warning(_msg)

                if job:
                    job.add_log(_msg)
                    job.state = "discarded"

        service.run(data, prepare, job=job)


    def _load_account_journal_map(self, data):
        ext_ids = set()
        for r in data:
            if r.get('id'):
                ext_ids.add(r.get('id'))

        if not ext_ids:
            return {}

        mappings = self.env['external.id.map'].search([
            ('external_id', 'in', list(ext_ids)),
            ('model', '=', 'account.journal')
        ])

        return {m.external_id: m.res_id for m in mappings}