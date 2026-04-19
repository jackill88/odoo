import logging
import json

from .master_import_registry import IMPORT_REGISTRY

_logger = logging.getLogger(__name__)


class FileDispatcher:
    """
    Routes files to correct importer based on filename.
    """
    _name = 'file.dispatcher'

    def __init__(self, env):
        self.env = env


    def _resolve_type(self, filename):
        name = filename.rsplit('.', 1)[0]  # remove .json

        for file_type in IMPORT_REGISTRY.keys():
            if name == file_type or name.startswith(file_type + "_"):
                return file_type

        return None
    
    def dispatch(self, file_type, content, job=None):
        try:
            data = json.loads(content)
        except Exception as e:
            if job:
                job.add_log(f"Invalid JSON in {file_type}: {e}")
                job.state = 'discarded'
            return

        try:
            importer_cls = IMPORT_REGISTRY[file_type]["importer"]
        except:
            msg = f"Unknown file type was provided: {file_type}"

            _logger.warning(msg)

            if job:
                job.add_log(msg)  
                job.state = 'discarded'

            return         

        _logger.info("Importing %s", file_type)
        importer_cls(self.env).run(data, job=job)