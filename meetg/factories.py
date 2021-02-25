"""
Help generate various Update objects used in testing
"""
import datetime, random

from meetg.api_types import (
    AnimationApiType, ChatApiType, DocumentApiType, MessageApiType, PhotoSizeApiType,
    StickerApiType, UpdateApiType, UserApiType,
)
from meetg.loging import get_logger
from meetg.utils import generate_random_string, parse_entities


logger = get_logger()

LAST_INT = 0


def get_next_int():
    """Always return a larger int. Useful to generate real-looking IDs"""
    global LAST_INT
    LAST_INT += 1
    return LAST_INT


class Factory:
    """
    Base class for any factory of a PTB object
    """
    api_type = None

    def __init__(self, tgbot):
        self.tgbot = tgbot

    def get_defaults(self):
        return {}

    def _filter_prefix(self, data, prefix):
        filtered = {}
        length = len(prefix)
        for key, val in data.items():
            if key.startswith(prefix):
                filtered[key[length:]] = val
        return filtered

    def _create_args(self, kwargs):
        validated_data = self.api_type(kwargs).validated_data
        args = self.get_defaults()
        args.update(validated_data)
        return args

    def create(self, **kwargs):
        args = self._create_args(kwargs)
        obj = self.api_type.ptb_class(**args)
        return obj


class UpdateFactory(Factory):
    """
    Base factory of Update objects
    """
    api_type = UpdateApiType
    update_type = None


class ChatFactory(Factory):
    api_type = ChatApiType

    def get_defaults(self):
        defaults = {
            'id': get_next_int(),
            'type': 'private',
        }
        return defaults


class UserFactory(Factory):
    api_type = UserApiType

    def get_defaults(self):
        defaults = {
            'id': get_next_int(),
            'first_name': 'Palin',
            'is_bot': False,
        }
        return defaults


class FileFactory(Factory):
    """
    Base factory for all the file-like Telegram types
    """
    def get_defaults(self):
        defaults = {
            'file_id': generate_random_string(98),
            'file_unique_id': generate_random_string(19),
            'file_size': random.randint(1, 999999),
        }
        return defaults


class PhotoSizeFactory(FileFactory):
    api_type = PhotoSizeApiType

    def get_defaults(self):
        defaults = super().get_defaults()
        defaults['width'] = random.randint(1, 500)
        defaults['height'] = random.randint(1, 500)
        return defaults


class AnimationFactory(FileFactory):
    api_type = AnimationApiType

    def get_defaults(self):
        defaults = super().get_defaults()
        defaults['duration'] = random.randint(1, 22)
        defaults['thumb'] = PhotoSizeFactory(self.tgbot).create()
        defaults['width'] = random.randint(1, 500)
        defaults['height'] = random.randint(1, 500)
        defaults['file_name'] = f'video_as_animation_{get_next_int()}.mp4'
        defaults['mime_type'] = 'video/mp4'
        return defaults


class StickerFactory(FileFactory):
    api_type = StickerApiType

    def get_defaults(self):
        defaults = super().get_defaults()
        defaults['thumb'] = PhotoSizeFactory(self.tgbot).create()
        defaults['width'] = random.randint(1, 500)
        defaults['height'] = random.randint(1, 500)
        defaults['is_animated'] = False
        return defaults


class DocumentFactory(FileFactory):
    api_type = DocumentApiType


class MessageFactory(Factory):
    api_type = MessageApiType

    def __init__(self, tgbot, message_type):
        super().__init__(tgbot)
        self.message_type = message_type

    def get_defaults(self):
        defaults = {
            'message_id': get_next_int(),
            'text': 'Spam',
            'date': datetime.datetime.now(),
            'bot': self.tgbot,
        }
        if self.message_type == 'edited_message':
            defaults['edit_date'] = datetime.datetime.now()
        return defaults

    def create(self, **kwargs):
        chat_args = self._filter_prefix(kwargs, 'chat__')
        from_user_args = self._filter_prefix(kwargs, 'from__')
        photo_size_args = self._filter_prefix(kwargs, 'photo__')
        document_args = self._filter_prefix(kwargs, 'document__')
        animation_args = self._filter_prefix(kwargs, 'animation__')
        sticker_args = self._filter_prefix(kwargs, 'sticker__')

        if 'id' in chat_args and chat_args['id'] > 0 and 'id' not in from_user_args:
            from_user_args['id'] = chat_args['id']

        args = self._create_args(kwargs)
        args['chat'] = ChatFactory(self.tgbot).create(**chat_args)
        args['from_user'] = UserFactory(self.tgbot).create(**from_user_args)
        args['entities'] = parse_entities(args['text'])

        if photo_size_args:
            args['photo'] = [PhotoSizeFactory(self.tgbot).create(**photo_size_args)]
        if document_args:
            args['document'] = DocumentFactory(self.tgbot).create(**document_args)
        if animation_args:
            args['animation'] = AnimationFactory(self.tgbot).create(**animation_args)
            document_args = args['animation'].to_dict()
            args['document'] = DocumentFactory(self.tgbot).create(**document_args)
        if sticker_args:
            args['sticker'] = StickerFactory(self.tgbot).create(**sticker_args)

        obj = self.api_type.ptb_class(**args)
        return obj


class MessageUpdateFactory(UpdateFactory):
    """
    Factory of an Update with a field of type 'Message'.
    It is a: message, edited_message, channel_post, and edited_channel_post
    """
    api_type = UpdateApiType

    update_type = 'Message'
    type_fields = MessageApiType.fields

    def __init__(self, tgbot, message_type):
        super().__init__(tgbot)
        self.message_type = message_type

    def create(self, **kwargs):
        message = MessageFactory(self.tgbot, self.message_type).create(**kwargs)
        update_obj = self.api_type.ptb_class(get_next_int(), **{self.message_type: message})
        return update_obj


class InlineQueryUpdateFactory(UpdateFactory):
    """
    Factory of an Update with a field of type 'InlineQuery'
    """
    update_type = 'InlineQuery'


class ChosenInlineResultUpdateFactory(UpdateFactory):
    """
    Factory of an Update with a field of type 'ChosenInlineResult'
    """
    update_type = 'ChosenInlineResult'
