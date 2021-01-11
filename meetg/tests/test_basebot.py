from parameterized import parameterized
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Filters

from meetg.botting import BaseBot
from meetg.tests.base import BaseTestCase


class TestBot(BaseBot):

    def set_handlers(self):
        handlers = (MessageHandler(Filters.text, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to any msg')


class TestBotSavingUsers(TestBot):
    save_users = True


class TestBotNotSavingUsers(TestBot):
    save_users = False


class TestBotSavingChats(TestBot):
    save_chats = True


class TestBotNotSavingChats(TestBot):
    save_chats = False


class SaveUserTest(BaseTestCase):
    """
    Bot must save new users by default
    """
    def setUp(self):
        super().setUp()
        self.bot = TestBotSavingUsers(mock=True)
        assert not self.bot.user_model.find()

    @parameterized.expand([
        ['private'],
        ['group'],
        ['supergroup'],
    ])
    def test_save_user(self, chat_type):
        self.bot.test_send('Spam', chat_type=chat_type)
        assert self.bot.user_model.find()


class NotSaveUserTest(BaseTestCase):
    """
    Bot must not save new users when save_users = False
    """
    def setUp(self):
        super().setUp()
        self.bot = TestBotNotSavingUsers(mock=True)
        assert not self.bot.user_model.find()

    @parameterized.expand([
        ['private'],
        ['group'],
        ['supergroup'],
    ])
    def test_not_save_user(self, chat_type):
        self.bot.test_send('Spam', chat_type=chat_type)
        assert not self.bot.user_model.find()


class SaveChatTest(BaseTestCase):
    """
    Bot must save new chats by default
    """
    def setUp(self):
        super().setUp()
        self.bot = TestBotSavingChats(mock=True)
        assert not self.bot.chat_model.find()

    @parameterized.expand([
        ['private'],
        ['group'],
        ['supergroup'],
    ])
    def test_save_chat(self, chat_type):
        self.bot.test_send('Spam', chat_type=chat_type)
        assert self.bot.chat_model.find()
