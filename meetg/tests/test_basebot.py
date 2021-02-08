import logging

from parameterized import parameterized
from telegram.ext import MessageHandler
from telegram.ext import Filters

import settings
from meetg.botting import BaseBot
from meetg.storage import (
    DefaultChatModel, DefaultMessageModel, DefaultUpdateModel, DefaultUserModel
)
from meetg.tests.base import MeetgBaseTestCase
from meetg.utils import get_update_type


class AnyHandlerBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def init_handlers(self):
        handlers = (MessageHandler(Filters.all, self.reply_any), )
        return handlers

    def reply_any(self, update_obj, context):
        chat_id = update_obj.effective_chat.id
        update_type = get_update_type(update_obj)
        self.send_message(chat_id, f'Update received: {update_type}')


class NoHandlerBot(BaseBot):
    """Bot without any handler (except InitialHandler)"""
    pass


class NoSaveUpdateModel(DefaultUpdateModel):
    """When use such a model, no objects are saved in storage"""
    save_fields = ()


class NoSaveMessageModel(DefaultMessageModel):
    """When use such a model, no objects are saved in storage"""
    save_fields = ()


class NoSaveUserModel(DefaultUserModel):
    """When use such a model, no objects are saved in storage"""
    save_fields = ()


class NoSaveChatModel(DefaultChatModel):
    """When use such a model, no objects are saved in storage"""
    save_fields = ()


class SaveObjTest(MeetgBaseTestCase):
    model_names = (
        ['Update'], ['Message'], ['User'], ['Chat'],
    )

    @parameterized.expand(model_names)
    def test_save(self, model_name):
        """Ensure the bot saves an object in storage"""
        bot = AnyHandlerBot(mock=True)
        model = getattr(bot, f'{model_name.lower()}_model')
        assert not model.find()
        bot.receive_message('Spam')
        assert model.find()

    @parameterized.expand(model_names)
    def test_no_save(self, model_name):
        """
        Ensure the bot doesn't save an object in storage
        """
        # apply model class with save_fields = ()
        no_save_model_class = f'meetg.tests.test_basebot.NoSave{model_name}Model'
        setattr(settings, f'{model_name.lower()}_model_class', no_save_model_class)

        bot = AnyHandlerBot(mock=True)
        model = getattr(bot, f'{model_name.lower()}_model')
        assert not model.find()
        bot.receive_message('Spam')
        assert not model.find()

    @parameterized.expand(model_names)
    def test_save_with_created_at(self, model_name):
        """Ensure the bot adds own timestamp when saves an object"""
        bot = AnyHandlerBot(mock=True)
        model = getattr(bot, f'{model_name.lower()}_model')
        bot.receive_message('Spam')
        assert 'meetg_created_at' in model.find_one()

    @parameterized.expand(model_names)
    def test_save_no_handlers(self, model_name):
        """Ensure the bot without any handler still saves an object"""
        bot = NoHandlerBot(mock=True)
        model = getattr(bot, f'{model_name.lower()}_model')
        assert not model.find()
        bot.receive_message('Spam')
        assert model.find()


class UpdateDbObjTest(MeetgBaseTestCase):
    """
    Tests about updating objects in database,
    not about PTB Update object
    """
    def test_update_message(self):
        """Ensure the bot updates message in storage when it is edited"""
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam', chat_id=1, message_id=1)
        assert bot.message_model.find_one({'message_id': 1, 'chat.id': 1, 'text': 'Spam'})

        bot.receive_edited_message('SpamSpamSpam', 1, 1)
        assert not bot.message_model.find_one({'message_id': 1, 'chat.id': 1, 'text': 'Spam'})
        assert bot.message_model.find_one({'message_id': 1, 'chat.id': 1, 'text': 'SpamSpamSpam'})


class StatTest(MeetgBaseTestCase):

    def test_stats_msg_broadcasted(self):
        settings.stats_to = (1, )
        bot = AnyHandlerBot(mock=True)
        bot._job_report_stats(None)
        assert bot.last_method.args['text'].startswith('@mock_username for the')


class AnswerTest(MeetgBaseTestCase):

    def test_text_answer_to_text(self):
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        assert bot.last_method.name == 'send_message'
        assert bot.last_method.args['chat_id'] == 1
        assert bot.last_method.args['text'] == 'Update received: message'

    def test_text_answer(self):
        bot = AnyHandlerBot(mock=True)
        bot.send_message(1, 'bot sends this')
        assert bot.last_method.name == 'send_message'
        assert bot.last_method.args['chat_id'] == 1
        assert bot.last_method.args['text'] == 'bot sends this'
