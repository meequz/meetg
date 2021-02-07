"""
Help generate various Update objects used in testing
"""
import datetime

from telegram import Chat, Message, Update, User

from meetg.loging import get_logger
from meetg.utils import parse_entities


logger = get_logger()

LAST_INT = 0


def get_next_int():
    """Always return a larger int. Useful to generate real-looking IDs"""
    global LAST_INT
    LAST_INT += 1
    return LAST_INT


class UpdateFactory:
    """
    Base factory of Update objects
    """
    def __init__(self, tgbot):
        self.tgbot = tgbot

    def _validate(self, data):
        validated = {}
        for key in data:
            if key in self.parameters:
                validated[key] = data[key]
            else:
                logger.error('Wrong arg %s passed to %s update', key, self.name)
        return validated


class MessageUpdateFactory(UpdateFactory):
    """
    Factory of an Update with 'message' field
    """
    name = 'message'
    parameters = (
        # required
        'message_id',
        # optional
        'from', 'sender_chat', 'date', 'chat', 'forward_from', 'forward_from_chat',
        'forward_from_message_id', 'forward_signature', 'forward_sender_name', 'forward_date',
        'reply_to_message', 'via_bot', 'edit_date', 'media_group_id', 'author_signature', 'text',
        'entities', 'animation', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note',
        'voice', 'caption', 'caption_entities', 'contact', 'dice', 'game', 'poll', 'venue',
        'location', 'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo',
        'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
        'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message',
        'invoice', 'successful_payment', 'connected_website', 'passport_data',
        'proximity_alert_triggered', 'reply_markup',
    )
    defaults = (
        ('text', 'Spam'),
    )

    def create(self, text, **kwargs):
        validated = self._validate(kwargs)
        args = dict(self.defaults)
        args.update(validated)

        message_id = args.get('message_id', get_next_int())
        date = args.get('date', datetime.datetime.now())

        # replace with ChatFactory
        chat_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('chat__')}
        chat_args = {'id': 1, 'type': 'private'}  # default
        chat_args.update(chat_kwargs)
        chat = Chat(**chat_args)

        # replace with UserFactory
        from_user = User(id=get_next_int(), first_name='Palin', is_bot=False)
        entities = parse_entities(text)
        
        message = Message(
            message_id=message_id, text=text, date=date, chat=chat, from_user=from_user,
            entities=entities, bot=self.tgbot,
        )
        update_obj = Update(get_next_int(), message=message)
        return update_obj
