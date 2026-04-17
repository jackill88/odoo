import logging
import json

from .goods_importer import GoodsImporter
from .pricelist_importer import PricelistImporter

_logger = logging.getLogger(__name__)


class FileDispatcher:
    """
    Routes files to correct importer based on filename.
    """
    _name = 'file.dispatcher'

    def __init__(self, env):
        self.env = env

    def dispatch(self, filename, content, job=None):
        try:
            data = json.loads(content)
        except Exception as e:
            msg = f"Invalid JSON in {filename}: {e}"

            if job:
                job.add_log(msg)
                job.state = 'discarded'
            return

        if filename.startswith('goods'):
            _logger.info("Dispatching GOODS: %s", filename)
            GoodsImporter(self.env).run(data, job=job)

        elif filename.startswith('prices'):
            _logger.info("Dispatching PRICES: %s", filename)
            PricelistImporter(self.env).run(data, job=job)

        else:
            msg = f"Unknown file type was provided: {filename}"

            _logger.warning(msg)

            if job:
                job.add_log(msg)

            # 👇 important: DO NOT fail job
            return