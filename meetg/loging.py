import logging

import settings


_logger = None
_level = None
_file_path = None


def _create_logger():
    format_ = '%(asctime)s: %(message)s'
    logging.basicConfig(format='%(asctime)s: %(message)s')

    logger = logging.getLogger(__name__)
    logger.setLevel(settings.log_level)

    file_handler = logging.FileHandler(settings.log_path)
    file_handler.setFormatter(logging.Formatter(format_))
    logger.addHandler(file_handler)

    return logger


def _are_settings_updated():
    level_changed = _level != settings.log_level
    file_changed = _file_path != settings.log_path
    return level_changed or file_changed


def _update():
    global _level, _file_path
    _level = settings.log_level
    _file_path = settings.log_path


def get_logger():
    global _logger
    if _logger is None or _are_settings_updated():
        _logger = _create_logger()
        _update()
    return _logger
