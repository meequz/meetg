import logging

from telegram.ext import MessageHandler
from telegram.ext import Filters

import settings
from meetg.botting import BaseBot
from meetg.storage import DefaultUpdateModel
from meetg.tests.base import MeetgBaseTestCase


class AnyHandlerBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def set_handlers(self):
        handlers = (MessageHandler(Filters.all, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id = self.extract(update_obj, 'message.chat.id')
        self.send_message(chat_id, 'reply to any msg')


class NoHandlerBot(BaseBot):
    """Bot without any handler (except InitialHandler)"""
    pass


class NoSaveUpdateModel(DefaultUpdateModel):
    """When use such a model, no objects are saved in storage"""
    save_fields = ()


class SaveUpdateTest(MeetgBaseTestCase):

    def test_save_update(self):
        """Ensure the bot saves update object in storage"""
        bot = AnyHandlerBot(mock=True)
        assert not bot.update_model.find()
        bot.test_send('Spam')
        assert bot.update_model.find()

    def test_no_save_update(self):
        """Ensure the bot doesn't save update object in storage"""
        settings.update_model_class = 'meetg.tests.test_basebot.NoSaveUpdateModel'
        bot = AnyHandlerBot(mock=True)
        assert not bot.update_model.find()
        bot.test_send('Spam')
        assert not bot.update_model.find()

    def test_save_update_with_created_at(self):
        """Ensure the bot adds own timestamp when saves update object"""
        bot = AnyHandlerBot(mock=True)
        bot.test_send('Spam')
        assert 'meetg_created_at' in bot.update_model.find_one()

    def test_save_update_no_handlers(self):
        """Ensure the bot without any handler still saves update object"""
        bot = NoHandlerBot(mock=True)
        assert not bot.update_model.find()
        bot.test_send('Spam')
        assert bot.update_model.find()


class StatTest(MeetgBaseTestCase):

    def test_stats_msg_broadcasted(self):
        settings.stats_to = (1, )
        bot = AnyHandlerBot(mock=True)
        bot.job_stats(None)
        assert bot.api_text_sent.startswith('@mock_username for the')


class AnswerTest(MeetgBaseTestCase):

    def test_text_answer_to_text(self):
        bot = AnyHandlerBot(mock=True)
        bot.test_send('Spam')
        assert bot.api_method_called == 'send_message'
        assert bot.api_args_used['chat_id'] == 1
        assert bot.api_args_used['text'] == 'reply to any msg'

    def test_text_answer(self):
        bot = AnyHandlerBot(mock=True)
        bot.send_message(1, 'bot sends this')
        assert bot.api_method_called == 'send_message'
        assert bot.api_args_used['chat_id'] == 1
        assert bot.api_args_used['text'] == 'bot sends this'
