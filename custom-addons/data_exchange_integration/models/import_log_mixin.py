import logging

_logger = logging.getLogger(__name__)


class ImportLogMixin:
    """
    Mixin to standardize logging for import processes.
    """

    def log_info(self, message, **kwargs):
        _logger.info(self._format(message, **kwargs))

    def log_warning(self, message, **kwargs):
        _logger.warning(self._format(message, **kwargs))

    def log_error(self, message, **kwargs):
        _logger.error(self._format(message, **kwargs))

    def log_exception(self, message, **kwargs):
        _logger.exception(self._format(message, **kwargs))

    def _format(self, message, **kwargs):
        if kwargs:
            try:
                return message.format(**kwargs)
            except Exception:
                return f"{message} | {kwargs}"
        return message