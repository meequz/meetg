from parameterized import parameterized
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Filters

from meetg.botting import BaseBot
from meetg.tests.base import BaseTestCase


class TestBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def set_handlers(self):
        handlers = (MessageHandler(Filters.text, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to any msg')


class TestBotSavingObjects(TestBot):
    save_users = True
    save_chats = True
    save_messages = True


class TestBotNotSavingObjects(TestBot):
    save_users = False
    save_chats = False
    save_messages = False


class SaveObjectsTest(BaseTestCase):

    @parameterized.expand([
        ['user_model', 'private'], ['user_model', 'group'], ['user_model', 'supergroup'],
        ['chat_model', 'private'], ['chat_model', 'group'], ['chat_model', 'supergroup'],
        ['message_model', 'private'], ['message_model', 'group'], ['message_model', 'supergroup'],
    ])
    def test_save_object(self, model_name, chat_type):
        """
        Ensure the bot saves users, chats and messages in DB
        """
        self.bot = TestBotSavingObjects(mock=True)
        model = getattr(self.bot, model_name)
        assert not model.find()
        self.bot.test_send('Spam', chat_type=chat_type)
        assert model.find()

    @parameterized.expand([
        ['user_model', 'private'], ['user_model', 'group'], ['user_model', 'supergroup'],
        ['chat_model', 'private'], ['chat_model', 'group'], ['chat_model', 'supergroup'],
        ['message_model', 'private'], ['message_model', 'group'], ['message_model', 'supergroup'],
    ])
    def test_not_save_object(self, model_name, chat_type):
        """
        Ensure the bot does NOT save users, chats and messages in DB
        """
        self.bot = TestBotNotSavingObjects(mock=True)
        model = getattr(self.bot, model_name)
        assert not model.find()
        self.bot.test_send('Spam', chat_type=chat_type)
        assert not model.find()
