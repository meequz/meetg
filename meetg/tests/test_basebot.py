from telegram.ext import MessageHandler
from telegram.ext import Filters

import settings
from meetg.botting import BaseBot
from meetg.storage import DefaultUpdateModel
from meetg.tests.base import BaseTestCase


class TestBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def set_handlers(self):
        handlers = (MessageHandler(Filters.all, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id, msg_id, user, text = self.extract(update_obj)
        self.send_msg(chat_id, 'reply to any msg')


class NoSaveUpdateModel(DefaultUpdateModel):
    """If use such a model, no objects are saved in storage"""
    save_fields = ()


class SaveUpdateTest(BaseTestCase):

    def test_save_update(self):
        """Ensure the bot saves update object in storage"""
        self.bot = TestBot(mock=True)
        model = self.bot.update_model

        assert not model.find()
        self.bot.test_send('Spam')
        assert model.find()

    def test_no_save_update(self):
        """Ensure the bot doesn't save update object in storage"""
        settings.update_model_class = 'meetg.tests.test_basebot.NoSaveUpdateModel'
        self.bot = TestBot(mock=True)
        model = self.bot.update_model

        assert not model.find()
        self.bot.test_send('Spam')
        assert not model.find()

    def test_save_update_with_created_at(self):
        """Ensure the bot adds own timestamp when saves update object"""
        self.bot = TestBot(mock=True)
        model = self.bot.update_model
        self.bot.test_send('Spam')
        assert 'meetg_created_at' in model.find_one()
