from telegram.ext import MessageHandler
from telegram.ext import Filters

import settings
from meetg.botting import BaseBot
from meetg.storage import DefaultUpdateModel
from meetg.tests.base import MeetgBaseTestCase


class TestBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def set_handlers(self):
        handlers = (MessageHandler(Filters.all, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id = self.proceed(update_obj, 'message.chat.id')
        self.send_msg(chat_id, 'reply to any msg')


class NoSaveUpdateModel(DefaultUpdateModel):
    """If use such a model, no objects are saved in storage"""
    save_fields = ()


class SaveUpdateTest(MeetgBaseTestCase):

    def test_save_update(self):
        """Ensure the bot saves update object in storage"""
        bot = TestBot(mock=True)
        assert not bot.update_model.find()
        bot.test_send('Spam')
        assert bot.update_model.find()

    def test_no_save_update(self):
        """Ensure the bot doesn't save update object in storage"""
        settings.update_model_class = 'meetg.tests.test_basebot.NoSaveUpdateModel'
        bot = TestBot(mock=True)
        assert not bot.update_model.find()
        bot.test_send('Spam')
        assert not bot.update_model.find()

    def test_save_update_with_created_at(self):
        """Ensure the bot adds own timestamp when saves update object"""
        bot = TestBot(mock=True)
        bot.test_send('Spam')
        assert 'meetg_created_at' in bot.update_model.find_one()


class StatTest(MeetgBaseTestCase):

    def test_stats_msg_broadcasted(self):
        settings.stats_to = (1, )
        bot = TestBot(mock=True)
        bot.job_stats(None)
        assert bot.api_text_sent.startswith('@mock_username for the')
