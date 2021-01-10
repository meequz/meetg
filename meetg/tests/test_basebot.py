from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Filters

from meetg.botting import BaseBot
from meetg.tests.base import BaseTestCase


class TestBotSavingUsers(BaseBot):

    def set_handlers(self):
        handlers = (
            CommandHandler('start', self.reply_start),
            MessageHandler(Filters.text, self.reply_any),
        )
        return handlers

    def reply_start(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to start')

    def reply_any(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to any other')


class TestBotNotSavingUsers(BaseBot):
    save_users = False

    def set_handlers(self):
        handlers = (
            CommandHandler('start', self.reply_start),
        )
        return handlers

    def reply_start(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to start')


class BaseBotTest(BaseTestCase):

    def test_save_user(self):
        """
        Bot must save new users by default
        """
        self.bot = TestBotSavingUsers(mock=True)

        users = self.bot.user_model.get()
        assert not users

        self.bot.test_send('/start')
        users = self.bot.user_model.get()
        assert users

    def test_not_save_user(self):
        """
        Bot must not save new users when save_users = False
        """
        self.bot = TestBotNotSavingUsers(mock=True)

        users = self.bot.user_model.get()
        assert not users

        self.bot.test_send('/start')
        users = self.bot.user_model.get()
        assert not users
