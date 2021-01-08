import logging
import unittest

import settings
from meetg.utils import dict_to_obj, import_string


class BotTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        settings.log_level = logging.WARNING
        self.bot = create_mock_bot()
        self.bot._db.drop_all()

    def tearDown(self):
        super().tearDown()
        self.bot._db.drop_all()


class UpdaterBotMock:
    
    def get_me(self):
        me = dict_to_obj('Me', {'username': 'mock_username'})
        return me


def create_mock_bot():
    Bot = import_string(settings.bot_class)
    DB = import_string(settings.db_class)
    db = DB(settings.mongo_db_name_test)
    bot = Bot(db, mock=True)
    return bot
