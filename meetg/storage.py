import time

import pymongo

import settings
from meetg.api_types import (
    ApiType, ChatApiType, MessageApiType, UpdateApiType, UserApiType,
)
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
        entry['meetg_modified_at'] = None
        return self.table.insert_one(entry)

    def update(self, pattern, new_data):
        new_data['meetg_modified_at'] = time.time()  # needs testing
        return self.table.update_many(pattern, {'$set': new_data})

    def update_one(self, pattern, new_data):
        new_data['meetg_modified_at'] = time.time()  # needs testing
        return self.table.update_one(pattern, {'$set': new_data})

    def count(self, pattern=None):
        return self.table.count_documents(pattern or {})

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
    """Base class for default models"""

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
            if field in self.fields:
                validated[field] = data[field]
            else:
                logger.warning('Field %s doesn\'t belong to model %s', field, self.name)
        return validated

    def drop(self):
        result = self._storage.drop()
        return result

    def _log_create(self, data: dict):
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

    def update_one(self, pattern, new_data):
        updated = self._storage.update_one(pattern, new_data)
        return updated

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
        return f'received {received} {self.name_lower}s'


class ApiTypeModel(BaseDefaultModel):
    """Base model class for objects related to Bot API"""

    def _log_create(self, data: dict):
        id_field = self.api_type.id_field
        logger.info('Storage: %s %s created', self.name, data[id_field])

    def get_ptb_obj(self, update_obj):
        raise NotImplementedError

    def get_pattern(self, ptb_obj):
        raise NotImplementedError

    def is_equal(self, ptb_obj, db_obj):
        equal = True
        for key, val in ptb_obj.to_dict().items():
            if key in db_obj:
                if db_obj[key] != val:
                    equal = False
                    break
        return equal

    def save_from_update_obj(self, update_obj):
        """Create or update object in DB"""
        ptb_obj = self.get_ptb_obj(update_obj)
        if ptb_obj:
            pattern = self.get_pattern(ptb_obj)
            db_obj = self.find_one(pattern)
            if db_obj:
                if not self.is_equal(ptb_obj, db_obj):
                    self.update_one(pattern, ptb_obj.to_dict())
            else:
                self.create(ptb_obj.to_dict())


class DefaultUpdateModel(ApiTypeModel):
    api_type = UpdateApiType

    name = api_type.name
    fields = api_type.fields

    def save_from_update_obj(self, update_obj):
        data = update_obj.to_dict()
        return self.create(data)

    def get_ptb_obj(self, update_obj):
        return update_obj

    def get_pattern(self, ptb_obj):
        pattern = {self.api_type.id_field: ptb_obj.update_id}
        return pattern


class DefaultMessageModel(ApiTypeModel):
    api_type = MessageApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_message
        return ptb_obj

    def get_pattern(self, ptb_obj):
        pattern = {self.api_type.id_field: ptb_obj.message_id, 'chat.id': ptb_obj.chat.id}
        return pattern


class DefaultUserModel(ApiTypeModel):
    api_type = UserApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_user
        return ptb_obj

    def get_pattern(self, ptb_obj):
        pattern = {self.api_type.id_field: ptb_obj.id}
        return pattern


class DefaultChatModel(ApiTypeModel):
    api_type = ChatApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_chat
        return ptb_obj

    def get_pattern(self, ptb_obj):
        pattern = {self.api_type.id_field: ptb_obj.id}
        return pattern
