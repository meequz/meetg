import datetime, importlib, logging, os, unittest

from telegram import Chat, Message, Update, User

import settings
from meetg import default_settings
from meetg.loging import get_logger
from meetg.storage import db
from meetg.utils import dict_to_obj, import_string


class BaseTestCase(unittest.TestCase):

    def _reset_settings(self):
        importlib.reload(settings)

    def _reinit_loggers(self):
        import meetg.botting
        import meetg.storage
        logger = get_logger()
        meetg.botting.logger = logger
        meetg.storage.logger = logger

    def setUp(self):
        super().setUp()
        self._reset_settings()
        settings.is_test = True
        settings.log_level = logging.CRITICAL
        self._reinit_loggers()


class BaseStorageTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        db.drop()


class BotTestCase(BaseStorageTestCase):

    def setUp(self):
        super().setUp()
        Bot = import_string(settings.bot_class)
        self.bot = Bot()


class JobQueueMock:
    """A mock to use in tests"""

    def run_daily(self, callback, period):
        pass

    def run_repeating(self, callback, period):
        pass

    def run_monthly(self, callback, period):
        pass

    def run_once(self, callback, period):
        pass


class TgBotMock:
    """A mock for PTB Bot"""
    username = 'mock_username'

    def __getattr__(self, name):
        pass

    def get_me(self):
        me = dict_to_obj('Me', {'username': self.username})
        return me


class UpdaterMock:
    """A mock for PTB Updater"""

    def __init__(self, *args, **kwargs):
        self.job_queue = JobQueueMock()
        self.bot = TgBotMock()


def get_sample(sample_fname):
    """Return content of one of the sample files"""
    path = os.path.join(settings._src_path, 'meetg', 'tests', 'samples', sample_fname)
    with open(path, 'rb') as f:
        sample = f.read()
    return sample
