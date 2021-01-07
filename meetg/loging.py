import logging

import settings


def get_logger():
    format_ = '%(asctime)s: %(message)s'
    logging.basicConfig(format='%(asctime)s: %(message)s')

    logger = logging.getLogger(__name__)
    logger.setLevel(settings.log_level)

    file_handler = logging.FileHandler(settings.log_path)
    file_handler.setFormatter(logging.Formatter(format_))
    logger.addHandler(file_handler)

    return logger
