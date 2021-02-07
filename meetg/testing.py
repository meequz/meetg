import datetime, importlib, logging, unittest

from telegram import Chat, Message, Update, User

import settings
from meetg import default_settings
from meetg.loging import get_logger
from meetg.storage import get_model_classes
from meetg.utils import dict_to_obj, import_string, parse_entities


class BaseTestCase(unittest.TestCase):

    def _reset_settings(self):
        importlib.reload(settings)

    def _drop_db(self):
        for model_class in get_model_classes():
            Model = import_string(model_class)
            Model(test=True).drop()

    def _reinit_loggers(self):
        import meetg.botting
        import meetg.storage
        logger = get_logger()
        meetg.botting.logger = logger
        meetg.storage.logger = logger

    def setUp(self):
        super().setUp()
        self._reset_settings()
        settings.log_level = logging.ERROR
        self._reinit_loggers()
        self._drop_db()

    def tearDown(self):
        super().tearDown()
        self._drop_db()


class BotTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        Bot = import_string(settings.bot_class)
        self.bot = Bot(mock=True)


class JobQueueMock:

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
