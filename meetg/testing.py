import datetime, logging, unittest

from telegram.chat import Chat
from telegram.message import Message
from telegram.messageentity import MessageEntity
from telegram.user import User

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
    username = 'mock_username'

    def get_me(self):
        me = dict_to_obj('Me', {'username': self.username})
        return me


def create_mock_bot():
    Bot = import_string(settings.bot_class)
    DB = import_string(settings.db_class)
    db = DB(settings.mongo_db_name_test)
    bot = Bot(db, mock=True)
    return bot


def create_test_message(string, bot):
    date = datetime.datetime.now()
    chat = Chat(1, 'private')
    user = User(id=1, first_name='Firstname', is_bot=False)

    entities = []
    if string.startswith('/'):
        entitiy = MessageEntity(
            type=MessageEntity.BOT_COMMAND,
            offset=0,
            length=len(string.split()[0]),
        )
        entities = [entitiy]

    message = Message(
        message_id=1, text=string, date=date, chat=chat, from_user=user, entities=entities,
        bot=bot,
    )
    return message
