import logging

from parameterized import parameterized

import settings
from meetg.botting import BaseBot
from meetg.storage import (
    DefaultChatModel, DefaultMessageModel, DefaultUpdateModel, DefaultUserModel
)
from meetg.tests.base import AnyHandlerBot, AnyHandlerBotCase, MeetgBaseTestCase


class NoHandlerBot(BaseBot):
    """Bot without any handler (except InitialHandler)"""
    pass


class NoSaveUpdateModel(DefaultUpdateModel):
    """When use such a model, no objects are saved in storage"""
    fields = ()


class NoSaveMessageModel(DefaultMessageModel):
    """When use such a model, no objects are saved in storage"""
    fields = ()


class NoSaveUserModel(DefaultUserModel):
    """When use such a model, no objects are saved in storage"""
    fields = ()


class NoSaveChatModel(DefaultChatModel):
    """When use such a model, no objects are saved in storage"""
    fields = ()


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
        # apply model class with fields = ()
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


class UpdateDbObjTest(AnyHandlerBotCase):
    """
    Tests about updating objects in database,
    not about PTB Update object
    """
    def test_update_message(self):
        """Ensure bot updates the message in storage when it is edited"""
        self.bot.receive_message('Test Spam', chat__id=1, message_id=1)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'Test Spam'}
        assert self.bot.message_model.find_one(query)

        self.bot.receive_edited_message('SpamSpamSpam', 1, 1)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'Test Spam'}
        assert not self.bot.message_model.find_one(query)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'SpamSpamSpam'}
        assert self.bot.message_model.find_one(query)

    def test_update_user(self):
        """Ensure the bot updates user in storage"""
        self.bot.receive_message('Test Spam', from__id=531, from__username='palin')
        assert self.bot.user_model.find_one({'id': 531, 'username': 'palin'})

        self.bot.receive_message('Another Spam', from__id=531, from__username='jones')
        assert self.bot.user_model.count() == 1
        assert not self.bot.user_model.find_one({'id': 531, 'username': 'palin'})
        assert self.bot.user_model.find_one({'id': 531, 'username': 'jones'})

    def test_update_chat(self):
        """Ensure the bot updates chat in storage"""
        self.bot.receive_message('Spam', chat__id=642, chat__first_name='Palin')
        assert self.bot.chat_model.find_one({'id': 642, 'first_name': 'Palin'})

        self.bot.receive_message('More Spam', chat__id=642, chat__first_name='Jones')
        assert self.bot.chat_model.count() == 1
        assert not self.bot.chat_model.find_one({'id': 642, 'first_name': 'Palin'})
        assert self.bot.chat_model.find_one({'id': 642, 'first_name': 'Jones'})

    def test_save_with_modified_at(self):
        """Ensure the bot adds own timestamp when updates an object"""
        self.bot.receive_message('Spam', from__id=531, from__username='palin')
        assert self.bot.user_model.count() == 1
        assert not self.bot.user_model.find_one()['meetg_modified_at']

        self.bot.receive_message('More Spam', from__id=531, from__username='jones')
        assert self.bot.user_model.count() == 1
        assert self.bot.user_model.find_one()['meetg_modified_at']

    def test_not_updated_when_the_same(self):
        """Ensure the bot doesn't update the object if it not changed"""
        self.bot.receive_message('Spam', from__id=531)
        assert not self.bot.user_model.find_one()['meetg_modified_at']

        self.bot.receive_message('More Spam', from__id=531)
        assert not self.bot.user_model.find_one()['meetg_modified_at']


class StatTest(AnyHandlerBotCase):

    def setUp(self):
        super().setUp()
        settings.stats_to = (1, )

    def test_stats_msg_broadcasted(self):
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        assert self.bot.last_method.args['text'].startswith('@mock_username for the')

    def test_number_of_api_objects_in_stats(self):
        self.bot.receive_message('Spam')
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        broadcasted = self.bot.last_method.args['text']
        assert 'stored 1 new chats' in broadcasted
        assert 'stored 1 new messages' in broadcasted
        assert 'stored 1 new updates' in broadcasted
        assert 'stored 1 new users' in broadcasted

    def test_job_time_in_stats(self):
        self.bot.receive_message('Spam')
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        stats_job()
        broadcasted = self.bot.last_method.args['text']
        assert '_job_report_stats took' in broadcasted

    def test_no_action_if_empty_stats_to(self):
        settings.stats_to = ()
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        assert not self.bot.last_method


class AnswerTest(AnyHandlerBotCase):

    def test_text_answer_to_text(self):
        self.bot.receive_message('Spam')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_method.args['text'] == 'Update received: message'

    def test_text_answer(self):
        self.bot.send_message(1, 'bot sends this')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_method.args['chat_id'] == 1
        assert self.bot.last_method.args['text'] == 'bot sends this'
