import logging
from io import BytesIO

from parameterized import parameterized

import settings
from meetg.botting import BaseBot
from meetg.storage import (
    DefaultChatModel, DefaultMessageModel, DefaultUpdateModel, DefaultUserModel
)
from meetg.tests.base import AnyHandlerBot, AnyHandlerBotCase, MeetgBaseTestCase
from meetg.testing import get_sample


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
        assert not model.count()
        bot.receive_message('Spam')
        assert model.count()

    @parameterized.expand(model_names)
    def test_no_save(self, model_name):
        """
        Ensure the bot doesn't save an object in storage if 'fields' are empty
        """
        # apply model class with fields = ()
        no_save_model_class = f'meetg.tests.test_basebot.NoSave{model_name}Model'
        setattr(settings, f'{model_name.lower()}_model_class', no_save_model_class)

        bot = AnyHandlerBot(mock=True)
        model = getattr(bot, f'{model_name.lower()}_model')
        assert not model.count()
        bot.receive_message('Spam')
        assert not model.count()

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
        assert not model.count()
        bot.receive_message('Spam')
        assert model.count()


class UpdateModelWithOnlyUpdateId(DefaultUpdateModel):
    fields = ('update_id', )


class UpdateModelWithOnlyMessage(DefaultUpdateModel):
    fields = ('message', )


class MessageModelWithOnlyMessageId(DefaultMessageModel):
    fields = ('message_id', )


class MessageModelWithOnlyDate(DefaultMessageModel):
    fields = ('date', )


class UserModelWithOnlyId(DefaultUserModel):
    fields = ('id', )


class UserModelWithOnlyFirstName(DefaultUserModel):
    fields = ('first_name', )


class ChatModelWithOnlyId(DefaultChatModel):
    fields = ('id', )


class ChatModelWithOnlyType(DefaultChatModel):
    fields = ('type', )


class SaveOnlySpecifiedFields(MeetgBaseTestCase):

    def test_save_update_with_only_update_id(self):
        settings.update_model_class = f'meetg.tests.test_basebot.UpdateModelWithOnlyUpdateId'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_update = bot.update_model.find_one()
        assert 'update_id' in db_update
        assert 'message' not in db_update

    def test_save_update_with_only_message(self):
        settings.update_model_class = f'meetg.tests.test_basebot.UpdateModelWithOnlyMessage'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_update = bot.update_model.find_one()
        assert 'message' in db_update
        assert 'update_id' not in db_update

    def test_save_message_with_only_message_id(self):
        settings.message_model_class = f'meetg.tests.test_basebot.MessageModelWithOnlyMessageId'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_message = bot.message_model.find_one()
        assert 'message_id' in db_message
        assert 'date' not in db_message
        assert 'chat' not in db_message

    def test_save_message_with_only_date(self):
        settings.message_model_class = f'meetg.tests.test_basebot.MessageModelWithOnlyDate'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_message = bot.message_model.find_one()
        assert 'date' in db_message
        assert 'message_id' not in db_message
        assert 'chat' not in db_message

    def test_save_user_with_only_id(self):
        settings.user_model_class = f'meetg.tests.test_basebot.UserModelWithOnlyId'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_user = bot.user_model.find_one()
        assert 'id' in db_user
        assert 'is_bot' not in db_user
        assert 'first_name' not in db_user

    def test_save_user_with_only_first_name(self):
        settings.user_model_class = f'meetg.tests.test_basebot.UserModelWithOnlyFirstName'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_user = bot.user_model.find_one()
        assert 'first_name' in db_user
        assert 'id' not in db_user
        assert 'is_bot' not in db_user

    def test_save_chat_with_only_id(self):
        settings.chat_model_class = f'meetg.tests.test_basebot.ChatModelWithOnlyId'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_user = bot.chat_model.find_one()
        assert 'id' in db_user
        assert 'type' not in db_user

    def test_save_chat_with_only_type(self):
        settings.chat_model_class = f'meetg.tests.test_basebot.ChatModelWithOnlyType'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam')
        db_user = bot.chat_model.find_one()
        assert 'type' in db_user
        assert 'id' not in db_user


class MessageModelWithTwoFields(DefaultMessageModel):
    fields = ('message_id', 'text', 'chat')


class UserModelWithTwoFields(DefaultUserModel):
    fields = ('id', 'is_bot')


class UpdateOnlySpecifiedFields(AnyHandlerBotCase):

    def test_update_message_with_two_fields(self):
        settings.message_model_class = f'meetg.tests.test_basebot.MessageModelWithTwoFields'
        bot = AnyHandlerBot(mock=True)

        bot.receive_message('Spam 1', chat__id=1, message_id=1)
        last_db_message = bot.message_model.find_one()
        assert 'date' not in last_db_message
        assert last_db_message['text'] == 'Spam 1'

        bot.receive_edited_message('SpamSpamSpam 2', 1, 1)
        last_db_message = bot.message_model.find_one()
        assert 'date' not in last_db_message
        assert 'delete_chat_photo' not in last_db_message
        assert last_db_message['text'] == 'SpamSpamSpam 2'

    def test_update_user_with_two_fields(self):
        settings.user_model_class = f'meetg.tests.test_basebot.UserModelWithTwoFields'
        bot = AnyHandlerBot(mock=True)
        bot.receive_message('Spam', from__id=1, from__first_name='Toip')
        assert 'first_name' not in bot.user_model.find_one()
        bot.receive_message('Spam', from__id=1, from__first_name='Gbossu')
        assert 'first_name' not in bot.user_model.find_one()


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

    def test_answer_text(self):
        self.bot.send_message(1, 'bot sends this')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_method.args['chat_id'] == 1
        assert self.bot.last_method.args['text'] == 'bot sends this'

    def test_answer_image(self):
        self.bot.send_photo(1, photo=get_sample('png_2px.png'))
        assert self.bot.last_method.name == 'send_photo'
        assert isinstance(self.bot.last_method.args['photo'], bytes)

    def test_answer_gif(self):
        self.bot.send_document(1, document=get_sample('gif_animation.gif'))
        assert self.bot.last_method.name == 'send_document'
        assert isinstance(self.bot.last_method.args['document'], bytes)

    def test_answer_mp4_animation(self):
        self.bot.send_animation(1, animation=get_sample('no_sound.mp4'))
        assert self.bot.last_method.name == 'send_animation'
        assert isinstance(self.bot.last_method.args['animation'], bytes)


class ReceiveTest(AnyHandlerBotCase):

    def test_receive_text(self):
        self.bot.receive_message('Spam')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.text == 'Spam'

    def test_receive_image(self):
        self.bot.receive_message(photo__file_id='BfaqFvb')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.photo[0].file_id == 'BfaqFvb'

    def test_receive_gif(self):
        self.bot.receive_message(document__mime_type='image/gif')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.document.mime_type == 'image/gif'

    def test_receive_mp4_animation(self):
        self.bot.receive_message(animation__mime_type='video/mp4')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.animation.mime_type == 'video/mp4'

    def test_receive_animated_sticker(self):
        self.bot.receive_message(sticker__is_animated=True)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.sticker.is_animated == True

    def test_receive_not_animated_sticker(self):
        self.bot.receive_message(sticker__is_animated=False)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.sticker.is_animated == False

    def test_receive_audio(self):
        self.bot.receive_message(audio__duration=15)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.audio.duration == 15

    def test_receive_video(self):
        self.bot.receive_message(video__duration=21)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.video.duration == 21

    def test_receive_contact(self):
        self.bot.receive_message(contact__phone_number='+123456789')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.contact.phone_number == '+123456789'

    def test_receive_location(self):
        self.bot.receive_message(location__longitude=-36, location__latitude=45)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.location.longitude == -36
        assert self.bot.last_update.effective_message.location.latitude == 45
