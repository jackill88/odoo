import logging

from typing import Tuple, Optional
from collections import defaultdict

_logger = logging.getLogger(__name__)


class ImporterService:
    """
    Generic high-performance importer:
    - idempotent via external.id.map
    - batch processing
    - preloaded mappings
    - chunk commits
    """

    def __init__(self, env, model_name, external_field='id', batch_size=500):
        self.env = env
        self.model_name = model_name
        self.Model = env[model_name]
        self.Map = env['external.id.map']

        self.external_field = external_field
        self.batch_size = batch_size

    # =============================
    # PUBLIC ENTRYPOINT
    # =============================

    def run(self, records, prepare_vals, job=None):
        total = len(records)
        _logger.info("Import %s: %s records", self.model_name, total)
        
        _successfully_processed = 0
        _successfully_added = 0
        _successfully_updated = 0

        for i in range(0, total, self.batch_size):
            chunk = records[i:i + self.batch_size]

            try:
                _no_created, _no_updated = self._process_chunk(chunk, prepare_vals, job)
                self.env.cr.commit()

                _successfully_added += _no_created
                _successfully_updated += _no_updated

                _successfully_processed += ((_no_created or 0)+(_no_updated or 0))

            except Exception as e:
                _msg = f"Chunk failed for {self.model_name}: {str(e)}"
                _logger.exception(_msg)

                if job:
                    job.add_log(_msg)

        if job:
            job.add_log(f"{self.model_name}: successfully processed {_successfully_processed} out of {total} records. Added: {_successfully_added}, updated: {_successfully_updated}")

    # =============================
    # CORE CHUNK PROCESSING
    # =============================

    def _process_chunk(self, chunk, prepare_vals, job=None)->Tuple[int, int]:
        external_ids = [r[self.external_field] for r in chunk]

        mapping_dict = self._load_mappings(external_ids)

        to_create = []
        to_update = []

        for rec in chunk:
            ext_id = str(rec[self.external_field])

            try:
                vals = prepare_vals(rec)

                if ext_id in mapping_dict:
                    to_update.append((mapping_dict[ext_id], vals))
                else:
                    to_create.append((ext_id, vals))

            except Exception as e:
                _logger.warning("Skipping %s: %s", ext_id, str(e))

        created, no_created = self._bulk_create(to_create)
        no_updated = self._bulk_update(to_update)

        self._create_mappings(created)

        return no_created, no_updated


    # =============================
    # MAPPING LAYER
    # =============================

    def _load_mappings(self, external_ids):
        if not external_ids:
            return {}

        records = self.Map.search([
            ('external_id', 'in', external_ids),
            ('model', '=', self.model_name)
        ])

        return {r.external_id: r.res_id for r in records}

    def _create_mappings(self, created_records):
        if not created_records:
            return

        vals = [{
            'external_id': ext_id,
            'model': self.model_name,
            'res_id': rec.id,
        } for ext_id, rec in created_records]

        self.Map.create(vals)
        _logger.info('Created')

    # =============================
    # ORM OPERATIONS
    # =============================

    def _is_simple_vals(self, vals):
        """helper function to define whether to use grouping strategy or not"""
        return all(not isinstance(v, (list, dict, set)) for v in vals.values())

    def _bulk_create(self, to_create)->Tuple[list, int]:
        if not to_create:
            return ([], 0)

        vals_list = [vals for _, vals in to_create]
        records = self.Model.create(vals_list)

        ret = list(zip([ext for ext, _ in to_create], records))

        return (ret, len(ret))

    def _bulk_update(self, to_update)->int:
        if not to_update:
            return 0
        
        simple_grouped = defaultdict(list)
        complex_updates = []

        for rec_id, vals in to_update:
            if self._is_simple_vals(vals):
                simple_grouped[frozenset(vals.items())].append(rec_id)
            else:
                complex_updates.append((rec_id, vals))

        _no_updated = 0

        # update grouped items (hashable)
        for vals_key, ids in simple_grouped.items():
            vals_to_write = dict(vals_key)
            _ = vals_to_write.pop('id', None)
            self.Model.browse(ids).write(vals_to_write)
            _no_updated += len(ids)

        # update complex items (non-hashable)
        for rec_id, vals in complex_updates:
            vals.pop('id', None)
            self.Model.browse(rec_id).write(vals)
            _no_updated +=1

        return _no_updated