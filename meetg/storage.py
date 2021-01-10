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
    """Wrapper for MongoDB collection methods"""

    def __init__(self, db_name, table_name, host='localhost', port=27017):
        super().__init__(db_name, table_name, host, port)
        self.client = pymongo.MongoClient(host=host, port=port)
        self.db = getattr(self.client, db_name)
        self.table = getattr(self.db, table_name)

    def create(self, entry):
        return self.table.insert_one(entry)

    def update(self, pattern, update):
        return self.table.update_many(pattern, update)

    def update_one(self, pattern, update):
        return self.table.update_one(pattern, update)

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


class DefaultUserModel:
    fields = (
        # required
        'chat_id', 'first_name', 'is_bot',
        # optional
        'last_name', 'username', 'language_code', 'phone_number', 'lat', 'lon',
        'can_join_groups', 'can_read_all_group_messages', 'supports_inline_queries',
    )

    def __init__(self, test=False):
        if test:
            db_name = settings.db_name_test
        else:
            db_name = settings.db_name

        Storage = import_string(settings.storage_class)
        self._storage = Storage(
            db_name=db_name, table_name=settings.user_table, host=settings.db_host,
            port=settings.db_port,
        )

    def _validate(self, **data):
        validated_data = {field: data[field] for field in data if field in self.fields}
        return validated_data

    def drop(self):
        self._storage.drop()

    def create(self, **data):
        user_data = self._validate(**data)
        chat_id = user_data['chat_id']
        self._storage.create(user_data)
        logger.info('User %s added to DB', chat_id)
        return user_data

    def create_from_obj(self, tg_user):
        user_data = {
            'chat_id': tg_user.id,
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
            'is_bot': tg_user.is_bot,
            'language_code': tg_user.language_code,
        }
        user = self.create(**user_data)
        return user

    def update(self, chat_id, **data):
        user_data = self._validate(chat_id=chat_id, **data)
        result = self._storage.update_one({'chat_id': chat_id}, {'$set': user_data})
        user = self.get_one(chat_id)
        logger.info('User %s updated in DB', chat_id)
        return user

    def update_from_obj(self, tg_user):
        chat_id = tg_user.id
        user_data = {
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
            'is_bot': tg_user.is_bot,
            'language_code': tg_user.language_code,
        }
        user = self.update(chat_id, **user_data)
        return user

    def get_one(self, chat_id):
        return self._storage.find_one({'chat_id': chat_id})

    def get(self, pattern):
        return self._storage.find(pattern)
