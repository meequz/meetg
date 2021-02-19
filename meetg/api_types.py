"""
Universal classes describing Telegram Bot API types.
Useful in many places: storage, factories, etc
"""
from telegram import Chat, Message, PhotoSize, Update, User


class ApiType:
    """Base class for any API type class"""
    ptb_class = None

    def __init__(self, data):
        self.validated_data = self.validate(data)

    def validate(self, data):
        validated = {}
        for key in data:
            if key in self.fields:
                validated[key] = data[key]
        return validated

    def get_ptb(self):
        ptb_obj = self.ptb_class(**self.validated_data)
        return ptb_obj


class UpdateApiType(ApiType):
    name = 'Update'
    ptb_class = Update
    id_field = 'update_id'
    fields = (
        # required
        'update_id',
        # optional
        'message', 'edited_message', 'channel_post', 'edited_channel_post', 'inline_query',
        'chosen_inline_result', 'callback_query', 'shipping_query', 'pre_checkout_query', 'poll',
        'poll_answer',
    )


class MessageApiType(ApiType):
    name = 'Message'
    ptb_class = Message
    id_field = 'message_id'
    fields = (
        # required
        'message_id', 'date', 'chat',
        # optional
        'from', 'sender_chat', 'forward_from', 'forward_from_chat', 'forward_from_message_id',
        'forward_signature', 'forward_sender_name', 'forward_date', 'reply_to_message', 'via_bot',
        'edit_date', 'media_group_id', 'author_signature', 'text', 'entities', 'animation',
        'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'caption',
        'caption_entities', 'contact', 'dice', 'game', 'poll', 'venue', 'location',
        'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo',
        'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
        'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message',
        'invoice', 'successful_payment', 'connected_website', 'passport_data',
        'proximity_alert_triggered', 'reply_markup',
    )


class UserApiType(ApiType):
    name = 'User'
    ptb_class = User
    id_field = 'id'
    fields = (
        # required
        'id', 'is_bot', 'first_name',
        # optional
        'last_name', 'username', 'language_code', 'can_join_groups', 'can_read_all_group_messages',
        'supports_inline_queries',
    )


class ChatApiType(ApiType):
    name = 'Chat'
    ptb_class = Chat
    id_field = 'id'
    fields = (
        # required
        'id', 'type',
        # optional
        'title', 'username', 'first_name', 'last_name', 'photo', 'bio', 'description',
        'invite_link', 'pinned_message', 'permissions', 'slow_mode_delay', 'sticker_set_name',
        'can_set_sticker_set', 'linked_chat_id', 'location', 'all_members_are_administrators',
    )


class PhotoSizeApiType(ApiType):
    name = 'PhotoSize'
    ptb_class = PhotoSize
    id_field = 'file_id'
    fields = (
        'file_id', 'file_unique_id', 'width', 'height', 'file_size',
    )
