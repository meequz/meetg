import pymongo

import settings
from meetg.utils import import_string
from meetg.loging import get_logger


logger = get_logger()


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
        return self.table.insert_one(entry)

    def update(self, pattern, new_data):
        return self.table.update_many(pattern, {'$set': new_data})

    def update_one(self, pattern, new_data):
        return self.table.update_one(pattern, {'$set': new_data})

    def count(self, pattern=None):
        return self.table.count(pattern)

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
    settings_table_name = None
    tg_id_field = None

    def __init__(self, test=False):
        if test:
            db_name = settings.db_name_test
        else:
            db_name = settings.db_name

        table_name = getattr(settings, self.settings_table_name)
        Storage = import_string(settings.storage_class)
        self._storage = Storage(
            db_name=db_name, table_name=table_name, host=settings.db_host, port=settings.db_port,
        )

    def _validate(self, data):
        validated_data = {field: data[field] for field in data if field in self.save_fields}
        return validated_data

    def drop(self):
        return self._storage.drop()

    def create(self, obj_id, data):
        data = self._validate(data)
        data[self.db_id_field] = obj_id
        result = self._storage.create(data)
        logger.info('%s %s added to DB', self.name, obj_id)
        return result

    def create_from_obj(self, obj):
        obj_id = getattr(obj, self.tg_id_field)
        result = self.create(obj_id, obj.to_dict())
        return result

    def update(self, obj_id, data):
        data = self._validate(data)
        result = self._storage.update_one({self.db_id_field: obj_id}, data)
        logger.info('%s %s updated in DB', self.name, obj_id)
        return result

    def update_from_obj(self, obj):
        obj_id = getattr(obj, self.tg_id_field)
        result = self.update(obj_id, obj.to_dict())
        return result

    def find(self, pattern=None):
        return [obj for obj in self._storage.find(pattern)]

    def find_one(self, obj_id=None):
        pattern = None
        if obj_id:
            pattern = {self.db_id_field: obj_id}
        return self._storage.find_one(pattern)


class DefaultUserModel(BaseDefaultModel):
    """
    Model to save and read Users in database.
    Note that field for user.id called user_id, not id.
    Other fields have the same names as in PTB
    """
    name = 'User'
    settings_table_name = 'user_table'
    tg_id_field = 'id'
    db_id_field = 'user_id'
    fields = (
        # required
        'user_id', 'is_bot', 'first_name',
        # optional
        'last_name', 'username', 'language_code', 'can_join_groups', 'can_read_all_group_messages',
        'supports_inline_queries',
        # if the user share it
        'phone_number', 'lat', 'lon',
    )
    save_fields = fields


class DefaultChatModel(BaseDefaultModel):
    """
    Field for chat.id called chat_id, not id.
    """
    name = 'Chat'
    settings_table_name = 'chat_table'
    tg_id_field = 'id'
    db_id_field = 'chat_id'
    fields = (
        # required
        'chat_id', 'type',
        # optional
        'title', 'username', 'first_name', 'last_name', 'photo', 'bio', 'description',
        'invite_link', 'pinned_message', 'permissions', 'slow_mode_delay', 'sticker_set_name',
        'can_set_sticker_set', 'linked_chat_id', 'location',
    )
    save_fields = fields


class DefaultMessageModel(BaseDefaultModel):
    name = 'Message'
    settings_table_name = 'message_table'
    tg_id_field = 'message_id'
    db_id_field = 'message_id'
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
    save_fields = 'message_id', 'date', 'chat', 'from'
