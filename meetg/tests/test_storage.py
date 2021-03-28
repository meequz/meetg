import telegram
from parameterized import parameterized

import settings
from meetg.botting import BaseBot
from meetg.storage import (
    db, DefaultChatModel, DefaultMessageModel, DefaultUpdateModel, DefaultUserModel
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
    model_names = ['Update'], ['Message'], ['User'], ['Chat']

    @parameterized.expand(model_names)
    def test_save(self, model_name):
        """Ensure the bot saves an object in storage"""
        bot = AnyHandlerBot()
        model = getattr(db, f'{model_name}')
        assert not model.count()
        bot.receive_message('Spam')
        assert model.count()

    @parameterized.expand(model_names)
    def test_empty_fields(self, model_name):
        """
        Ensure the bot doesn't save an object in storage if 'fields' are empty
        """
        # apply model class with fields = ()
        no_save_model_path = f'meetg.tests.test_storage.NoSave{model_name}Model'
        setattr(settings, f'{model_name}_model', no_save_model_path)

        bot = AnyHandlerBot()
        model = getattr(db, f'{model_name}')
        assert not model.count()
        bot.receive_message('Spam')
        assert not model.count()

    @parameterized.expand(model_names)
    def test_store_api_types_false(self, model_name):
        """
        Ensure the bot doesn't save an object in storage if settings.store_api_types=False
        """
        settings.store_api_types = False
        bot = AnyHandlerBot()
        model = getattr(db, f'{model_name}')
        bot.receive_message('Spam')
        assert not model.count()

    @parameterized.expand(model_names)
    def test_save_with_created_at(self, model_name):
        """Ensure the bot adds own timestamp when saves an object"""
        bot = AnyHandlerBot()
        model = getattr(db, f'{model_name}')
        bot.receive_message('Spam')
        assert '_created_at' in model.find_one()

    @parameterized.expand(model_names)
    def test_save_no_handlers(self, model_name):
        """Ensure the bot without any handler still saves an object"""
        bot = NoHandlerBot()
        model = getattr(db, f'{model_name}')
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
        settings.Update_model = f'meetg.tests.test_storage.UpdateModelWithOnlyUpdateId'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_update = db.Update.find_one()
        assert 'update_id' in db_update
        assert 'message' not in db_update

    def test_save_update_with_only_message(self):
        settings.Update_model = f'meetg.tests.test_storage.UpdateModelWithOnlyMessage'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_update = db.Update.find_one()
        assert 'message' in db_update
        assert 'update_id' not in db_update

    def test_save_message_with_only_message_id(self):
        settings.Message_model = f'meetg.tests.test_storage.MessageModelWithOnlyMessageId'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_message = db.Message.find_one()
        assert 'message_id' in db_message
        assert 'date' not in db_message
        assert 'chat' not in db_message

    def test_save_message_with_only_date(self):
        settings.Message_model = f'meetg.tests.test_storage.MessageModelWithOnlyDate'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_message = db.Message.find_one()
        assert 'date' in db_message
        assert 'message_id' not in db_message
        assert 'chat' not in db_message

    def test_save_user_with_only_id(self):
        settings.User_model = f'meetg.tests.test_storage.UserModelWithOnlyId'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_user = db.User.find_one()
        assert 'id' in db_user
        assert 'is_bot' not in db_user
        assert 'first_name' not in db_user

    def test_save_user_with_only_first_name(self):
        settings.User_model = f'meetg.tests.test_storage.UserModelWithOnlyFirstName'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_user = db.User.find_one()
        assert 'first_name' in db_user
        assert 'id' not in db_user
        assert 'is_bot' not in db_user

    def test_save_chat_with_only_id(self):
        settings.Chat_model = f'meetg.tests.test_storage.ChatModelWithOnlyId'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_chat = db.Chat.find_one()
        assert 'id' in db_chat
        assert 'type' not in db_chat

    def test_save_chat_with_only_type(self):
        settings.Chat_model = f'meetg.tests.test_storage.ChatModelWithOnlyType'
        bot = AnyHandlerBot()
        bot.receive_message('Spam')
        db_chat = db.Chat.find_one()
        assert 'type' in db_chat
        assert 'id' not in db_chat


class MessageModelWithoutDate(DefaultMessageModel):
    fields = ('message_id', 'text', 'chat')


class UserModelWithTwoFields(DefaultUserModel):
    fields = ('id', 'is_bot')


class UpdateOnlySpecifiedFields(AnyHandlerBotCase):

    def test_update_message_with_two_fields(self):
        settings.Message_model = f'meetg.tests.test_storage.MessageModelWithoutDate'
        bot = AnyHandlerBot()

        bot.receive_message('Spam 1', chat__id=1, message_id=1)
        last_db_message = db.Message.find_one()
        assert 'date' not in last_db_message
        assert last_db_message['text'] == 'Spam 1'

        bot.receive_edited_message('SpamSpamSpam 2', 1, 1)
        last_db_message = db.Message.find_one()
        assert 'date' not in last_db_message
        assert 'delete_chat_photo' not in last_db_message
        assert last_db_message['text'] == 'SpamSpamSpam 2'

    def test_update_user_with_two_fields(self):
        settings.User_model = f'meetg.tests.test_storage.UserModelWithTwoFields'
        bot = AnyHandlerBot()
        bot.receive_message('Spam', from__id=1, from__first_name='Toip')
        assert 'first_name' not in db.User.find_one()
        bot.receive_message('Spam', from__id=1, from__first_name='Gbossu')
        assert 'first_name' not in db.User.find_one()


class UpdateDbObjTest(AnyHandlerBotCase):
    """
    Tests of updating objects in database,
    not about PTB Update object
    """
    def test_update_message(self):
        """Ensure bot updates the message in storage when it is edited"""
        self.bot.receive_message('Test Spam', chat__id=1, message_id=1)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'Test Spam'}
        assert db.Message.find_one(query)

        self.bot.receive_edited_message('SpamSpamSpam', 1, 1)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'Test Spam'}
        assert not db.Message.find_one(query)
        query = {'message_id': 1, 'chat.id': 1, 'text': 'SpamSpamSpam'}
        assert db.Message.find_one(query)

    def test_update_user(self):
        """Ensure the bot updates user in storage"""
        self.bot.receive_message('Test Spam', from__id=531, from__username='palin')
        assert db.User.find_one({'id': 531, 'username': 'palin'})

        self.bot.receive_message('Another Spam', from__id=531, from__username='jones')
        assert db.User.count() == 1
        assert not db.User.find_one({'id': 531, 'username': 'palin'})
        assert db.User.find_one({'id': 531, 'username': 'jones'})

    def test_update_chat(self):
        """Ensure the bot updates chat in storage"""
        self.bot.receive_message('Spam', chat__id=642, chat__first_name='Palin')
        assert db.Chat.find_one({'id': 642, 'first_name': 'Palin'})

        self.bot.receive_message('More Spam', chat__id=642, chat__first_name='Jones')
        assert db.Chat.count() == 1
        assert not db.Chat.find_one({'id': 642, 'first_name': 'Palin'})
        assert db.Chat.find_one({'id': 642, 'first_name': 'Jones'})

    def test_save_with_modified_at(self):
        """Ensure the bot adds own timestamp when updates an object"""
        self.bot.receive_message('Spam', from__id=531, from__username='palin')
        assert db.User.count() == 1
        assert not db.User.find_one()['_modified_at']

        self.bot.receive_message('More Spam', from__id=531, from__username='jones')
        assert db.User.count() == 1
        assert db.User.find_one()['_modified_at']

    def test_not_updated_when_the_same(self):
        """Ensure the bot doesn't update the object if it not changed"""
        self.bot.receive_message('Spam', from__id=531)
        assert not db.User.find_one()['_modified_at']

        self.bot.receive_message('More Spam', from__id=531)
        assert not db.User.find_one()['_modified_at']

    def test_only_one_msg_with_the_same_ids(self):
        self.bot.receive_message('Foo', chat__id=1, message_id=1)
        assert db.User.count() == 1

        self.bot.receive_message('Bar', chat__id=1, message_id=1)
        assert db.Message.count() == 1
        assert db.Message.find_one()['text'] == 'Bar'


class DeleteDbObjTest(AnyHandlerBotCase):
    """Tests of deleting objects in database"""

    def test_kicked(self):
        """
        Ensure bot mark the chat as _kicked_at in storage
        when got telegram.error.Unauthorized
        """
        # The bot received an update that it was added to a group
        new_chat_members = [{'is_bot': True, 'username': 'mock_username'}]
        self.bot.receive_message(chat__id=-1, new_chat_members=new_chat_members)
        assert db.Chat.count() == 1
        assert not db.Chat.find_one().get('_kicked_at')

        # bot received info that it was kicked from the group
        # (or the whole group was deleted, it looks the same for the bot)
        exception = telegram.error.Unauthorized('Forbidden: bot was kicked from the group chat')
        self.bot.send_message(-1, 'Spam', raise_exception=exception)
        assert db.Chat.find_one()['_kicked_at']
