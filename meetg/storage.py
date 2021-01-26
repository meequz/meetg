import time

import pymongo

import settings
from meetg.utils import get_unixtime_before_now, import_string
from meetg.loging import get_logger


logger = get_logger()


def get_model_classes():
    model_classes = [getattr(settings, k) for k in dir(settings) if k.endswith('_model_class')]
    return model_classes


class AbstractStorage:
    """Any other storage must be a subclass of this class"""

    def __init__(self, db_name, table_name, host, port):
        self.db_name = db_name
        self.table_name = table_name
        self.host = host
        self.port = port

    def create(self, entry):
        raise NotImplementedError

    def update(self, pattern, update):
        raise NotImplementedError

    def update_one(self, pattern, update):
        raise NotImplementedError

    def count(self, pattern=None):
        raise NotImplementedError

    def find(self, pattern=None):
        raise NotImplementedError

    def find_one(self, pattern=None):
        raise NotImplementedError

    def delete(self, pattern):
        raise NotImplementedError

    def delete_one(self, pattern):
        raise NotImplementedError

    def drop(self):
        raise NotImplementedError


class MongoStorage(AbstractStorage):
    """
    Wrapper for MongoDB collection methods. Is is some kind of an ORM.
    Another potential storage, e.g. PostgreStorage, have to implement the same methods,
    allowing the same args to them. But I'm not sure it will be handful.
    So methods and args may change in time.
    """
    def __init__(self, db_name, table_name, host='localhost', port=27017):
        super().__init__(db_name, table_name, host, port)
        self.client = pymongo.MongoClient(host=host, port=port)
        self.db = getattr(self.client, db_name)
        self.table = getattr(self.db, table_name)

    def create(self, entry):
        entry['meetg_created_at'] = time.time()
        return self.table.insert_one(entry)

    def update(self, pattern, new_data):
        new_data['meetg_modified_at'] = time.time()  # needs testing
        return self.table.update_many(pattern, {'$set': new_data})

    def update_one(self, pattern, new_data):
        new_data['meetg_modified_at'] = time.time()  # needs testing
        return self.table.update_one(pattern, {'$set': new_data})

    def count(self, pattern=None):
        return self.table.count_documents(pattern)

    def find(self, pattern=None):
        return self.table.find(pattern)

    def find_one(self, pattern=None):
        return self.table.find_one(pattern)

    def delete(self, pattern):
        return self.table.delete_many(pattern)

    def delete_one(self, pattern):
        return self.table.delete_one(pattern)

    def drop(self):
        return self.db.drop_collection(self.table_name)


class BaseDefaultModel:
    tg_id_field = None
    related_to_update = False

    def __init__(self, test=False):
        db_name = settings.db_name_test if test else settings.db_name
        Storage = import_string(settings.storage_class)
        self._storage = Storage(
            db_name=db_name, table_name=self.table_name,
            host=settings.db_host, port=settings.db_port,
        )

    @property
    def name_lower(self):
        return self.name.lower()

    @property
    def table_name(self):
        return f'{self.name_lower}_table'

    def _validate(self, data):
        validated = {}
        for field in data:
            if field in self.save_fields:
                validated[field] = data[field]
            else:
                logger.warning('Field %s doesn\'t belong to model %s', field, self.name)
        return validated

    def drop(self):
        result = self._storage.drop()
        return result

    def _log_create(self, data: dict):
        if self.tg_id_field:
            logger.info('Storage: %s %s created', self.name, data[self.tg_id_field])
        else:
            logger.info('Storage: %s created', self.name)

    def create(self, data: dict):
        data = self._validate(data)
        result = None
        if data:
            result = self._storage.create(data)
            self._log_create(data)
        return result

    def find(self, pattern=None):
        found = [obj for obj in self._storage.find(pattern)]
        return found

    def find_one(self, pattern=None):
        found = self._storage.find_one(pattern)
        return found

    def count(self, pattern=None):
        counted = self._storage.count(pattern)
        return counted

    def _get_created_for_last_day_pattern(self):
        pattern = {
            'meetg_created_at': {
                '$lt': time.time(),
                '$gte': get_unixtime_before_now(24),
            },
        }
        return pattern

    def get_day_report(self):
        pattern = self._get_created_for_last_day_pattern()
        received = self.count(pattern)
        return f'- received {received} {self.name_lower}s\n'


class DefaultUpdateModel(BaseDefaultModel):
    name = 'Update'
    tg_id_field = 'update_id'
    related_to_update = True
    fields = (
        # required
        'update_id',
        # optional
        'message', 'edited_message', 'channel_post', 'edited_channel_post', 'inline_query',
        'chosen_inline_result', 'callback_query', 'shipping_query', 'pre_checkout_query', 'poll',
        'poll_answer',
    )
    save_fields = fields

    def create_from_update_obj(self, update_obj):
        data = update_obj.to_dict()
        return self.create(data)


class DefaultMessageModel(BaseDefaultModel):
    name = 'Message'
    tg_id_field = 'message_id'
    related_to_update = True
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
    save_fields = fields

    def create_from_update_obj(self, update_obj):
        if update_obj.effective_message:
            data = update_obj.effective_message.to_dict()
            return self.create(data)


class DefaultUserModel(BaseDefaultModel):
    name = 'User'
    tg_id_field = 'id'
    related_to_update = True
    fields = (
        # required
        'id', 'is_bot', 'first_name',
        # optional
        'last_name', 'username', 'language_code', 'can_join_groups', 'can_read_all_group_messages',
        'supports_inline_queries',
    )
    save_fields = fields

    def create_from_update_obj(self, update_obj):
        if update_obj.effective_user:
            data = update_obj.effective_user.to_dict()
            return self.create(data)


class DefaultChatModel(BaseDefaultModel):
    name = 'Chat'
    tg_id_field = 'id'
    related_to_update = True
    fields = (
        # required
        'id', 'type',
        # optional
        'title', 'username', 'first_name', 'last_name', 'photo', 'bio', 'description',
        'invite_link', 'pinned_message', 'permissions', 'slow_mode_delay', 'sticker_set_name',
        'can_set_sticker_set', 'linked_chat_id', 'location', 'all_members_are_administrators',
    )
    save_fields = fields

    def create_from_update_obj(self, update_obj):
        if update_obj.effective_chat:
            data = update_obj.effective_chat.to_dict()
            return self.create(data)
