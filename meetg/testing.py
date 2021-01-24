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
        self.bot = create_mock_bot()


class JobQueueMock:

    def run_daily(self, callback, period):
        pass


class BotMock:
    username = 'mock_username'

    def get_me(self):
        me = dict_to_obj('Me', {'username': self.username})
        return me


class UpdaterMock:

    def __init__(self, *args, **kwargs):
        self.job_queue = JobQueueMock()
        self.bot = BotMock()


def create_mock_bot():
    Bot = import_string(settings.bot_class)
    bot = Bot(mock=True)
    return bot


def create_test_message(string, bot):
    date = datetime.datetime.now()
    chat = Chat(1, 'private')
    user = User(id=1, first_name='Firstname', is_bot=False)
    entities = parse_entities(string)
    message = Message(
        message_id=1, text=string, date=date, chat=chat, from_user=user, entities=entities,
        bot=bot,
    )
    return message


def create_chat_obj(chat_id=None, chat_type='private', title=None):
    if chat_type == 'private':
        chat_id = chat_id or 1
    elif chat_type in ('group', 'supergroup'):
        chat_id = chat_id or -1
    else:
        raise NotImplementedError
    chat = Chat(id=chat_id, type=chat_type, title=title)
    return chat


def create_user_obj(user_id=1, first_name='Michael', last_name='Palin', is_bot=False):
    user = User(id=user_id, first_name=first_name, last_name=last_name, is_bot=is_bot)
    return user


def create_message_obj(
        message_id=1, chat_type='private', text='spam', user_id=1, chat_id=None, bot=None,
        user_first_name='Michael', user_last_name=None, chat_title=None,
    ):
    """
    A helper to create fake message objects for testing purposes.
    Generate a private message by default
    """
    date = datetime.datetime.now()
    chat = create_chat_obj(chat_id=chat_id, chat_type=chat_type, title=chat_title)
    user = create_user_obj(
        user_id=user_id, first_name=user_first_name, last_name=user_last_name, is_bot=False,
    )
    entities = parse_entities(text)
    message = Message(
        message_id=message_id, text=text, date=date, chat=chat, from_user=user,
        entities=entities, bot=bot,
    )
    return message


def create_update_obj(
        update_id=1, message=None, message_id=1, chat_type='private', message_text='spam',
        user_id=1, chat_id=None, bot=None, user_first_name='Michael', user_last_name=None,
        chat_title=None,
    ):
    """
    A helper to create fake update objects for testing purposes.
    Generate an update with a private message by default
    """
    if message is None:
        message = create_message_obj(
            message_id=message_id, chat_type=chat_type, text=message_text, user_id=user_id,
            chat_id=chat_id, bot=bot, user_first_name=user_first_name,
            user_last_name=user_last_name, chat_title=chat_title,
        )
    update_obj = Update(update_id, message=message)
    return update_obj
