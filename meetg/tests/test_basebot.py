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


class SaveUsersTest(BaseTestCase):
    """
    Bot must save new users by default
    """
    def setUp(self):
        super().setUp()
        self.bot = TestBotSavingUsers(mock=True)
        assert not self.bot.user_model.find()

    def test_save_user_in_private(self):
        self.bot.test_send('Spam')
        assert self.bot.user_model.find()

    def test_save_user_in_group(self):
        self.bot.test_send('Spam', chat_type='group')
        assert self.bot.user_model.find()


class NotSaveUsersTest(BaseTestCase):
    """
    Bot must not save new users when save_users = False
    """
    def setUp(self):
        super().setUp()
        self.bot = TestBotNotSavingUsers(mock=True)
        assert not self.bot.user_model.find()

    def test_not_save_user_in_private(self):
        self.bot.test_send('Spam')
        assert not self.bot.user_model.find()

    def test_not_save_user_in_group(self):
        self.bot.test_send('Spam', chat_type='group')
        assert not self.bot.user_model.find()
