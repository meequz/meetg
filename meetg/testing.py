import datetime, logging, unittest

from telegram import Update
from telegram.chat import Chat
from telegram.message import Message
from telegram.messageentity import MessageEntity
from telegram.user import User

import settings
from meetg.utils import dict_to_obj, import_string


class BotTestCase(unittest.TestCase):

    def _drop_db(self):
        for model_class in settings.model_classes:
            Model = import_string(model_class)
            Model().drop()

    def setUp(self):
        super().setUp()
        settings.log_level = logging.WARNING
        self.bot = create_mock_bot()
        self._drop_db()

    def tearDown(self):
        super().tearDown()
        self._drop_db()


class UpdaterBotMock:
    username = 'mock_username'

    def get_me(self):
        me = dict_to_obj('Me', {'username': self.username})
        return me


def create_mock_bot():
    Bot = import_string(settings.bot_class)
    bot = Bot(mock=True)
    return bot


def _parse_entities(string):
    entities = []
    if string.startswith('/'):
        entity = MessageEntity(
            type=MessageEntity.BOT_COMMAND,
            offset=0,
            length=len(string.split()[0]),
        )
        entities.append(entity)
    return entities


def create_test_message(string, bot):
    date = datetime.datetime.now()
    chat = Chat(1, 'private')
    user = User(id=1, first_name='Firstname', is_bot=False)
    entities = _parse_entities(string)
    message = Message(
        message_id=1, text=string, date=date, chat=chat, from_user=user, entities=entities,
        bot=bot,
    )
    return message


def create_chat_obj(chat_id=None, chat_type='private'):
    if chat_id is None:
        if chat_type == 'private':
            chat_id = 1
        elif chat_type in ('group', 'supergroup'):
            chat_id = -1
    chat = Chat(chat_id, chat_type)
    return chat


def create_message_obj(
        message_id=1, chat_type='private', text='spam', user_id=1, chat_id=None, bot=None,
    ):
    """
    A helper to create fake update objects for testing purposes.
    Generate a private message by default
    """
    date = datetime.datetime.now()
    chat = create_chat_obj(chat_id=chat_id, chat_type=chat_type)
    user = User(id=user_id, first_name=f'User {user_id} first name', is_bot=False)
    entities = _parse_entities(text)
    message = Message(
        message_id=message_id, text=text, date=date, chat=chat, from_user=user,
        entities=entities, bot=bot,
    )
    return message


def create_update_obj(
        update_id=1, message=None, message_id=1, chat_type='private', message_text='spam',
        user_id=1, chat_id=None, bot=None,
    ):
    """
    A helper to create fake update objects for testing purposes.
    Generate an update with a private message by default
    """
    if message is None:
        message = create_message_obj(
            message_id=message_id, chat_type=chat_type, text=message_text, user_id=user_id,
            chat_id=chat_id, bot=bot,
        )
    update_obj = Update(update_id, message=message)
    return update_obj
