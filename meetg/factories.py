"""
Help generate various Update objects used in testing
"""
import datetime, random

from meetg.api_types import (
    AnimationApiType, AudioApiType, ChatApiType, ContactApiType, DocumentApiType, LocationApiType,
    MessageApiType, PhotoSizeApiType, StickerApiType, UpdateApiType, UserApiType, VideoApiType,
)
from meetg.loging import get_logger
from meetg.entities import parse_entities
from meetg.utils import generate_random_string


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

    def prefix_create(self, prefix, kwargs, force=False):
        args = self._filter_prefix(kwargs, prefix)
        obj = None
        if args or force:
            obj = self.create(**args)
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


class AudioFactory(FileFactory):
    api_type = AudioApiType

    def get_defaults(self):
        defaults = super().get_defaults()
        defaults['duration'] = random.randint(1, 500)
        return defaults


class VideoFactory(FileFactory):
    api_type = VideoApiType

    def get_defaults(self):
        defaults = super().get_defaults()
        defaults['width'] = random.randint(1, 500)
        defaults['height'] = random.randint(1, 500)
        defaults['duration'] = random.randint(1, 500)
        return defaults


class ContactFactory(Factory):
    api_type = ContactApiType

    def get_defaults(self):
        defaults = {
            'phone_number': '+' + str(random.randint(11111111111, 999999999999)),
            'first_name': 'Palin',
        }
        return defaults


class LocationFactory(Factory):
    api_type = LocationApiType

    def get_defaults(self):
        defaults = {
            'longitude': float(random.randint(-180, 180)),
            'latitude': float(random.randint(-90, 90)),
        }
        return defaults


class MessageFactory(Factory):
    api_type = MessageApiType

    def __init__(self, tgbot, message_type):
        super().__init__(tgbot)
        self.message_type = message_type

    def get_defaults(self):
        defaults = {
            'message_id': get_next_int(),
            'date': datetime.datetime.now(),
            'bot': self.tgbot,
        }
        if self.message_type == 'edited_message':
            defaults['edit_date'] = datetime.datetime.now()
        return defaults

    def create(self, **kwargs):
        chat__id = kwargs.get('chat__id', 0)
        if chat__id > 0 and 'from__id' not in kwargs:
            kwargs['from__id'] = chat__id

        args = self._create_args(kwargs)
        args['entities'] = parse_entities(args['text'])
        args['chat'] = ChatFactory(self.tgbot).prefix_create('chat__', kwargs, force=True)
        args['from_user'] = UserFactory(self.tgbot).prefix_create('from__', kwargs, force=True)
        args['document'] = DocumentFactory(self.tgbot).prefix_create('document__', kwargs)
        args['sticker'] = StickerFactory(self.tgbot).prefix_create('sticker__', kwargs)
        args['audio'] = AudioFactory(self.tgbot).prefix_create('audio__', kwargs)
        args['video'] = VideoFactory(self.tgbot).prefix_create('video__', kwargs)
        args['contact'] = ContactFactory(self.tgbot).prefix_create('contact__', kwargs)
        args['location'] = LocationFactory(self.tgbot).prefix_create('location__', kwargs)

        photo = PhotoSizeFactory(self.tgbot).prefix_create('photo__', kwargs)
        if photo:
            args['photo'] = [photo]

        args['animation'] = AnimationFactory(self.tgbot).prefix_create('animation__', kwargs)
        if args['animation']:
            args['document'] = DocumentFactory(self.tgbot).create(**args['animation'].to_dict())

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
        update = self.api_type.ptb_class(get_next_int(), **{self.message_type: message})
        return update


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
