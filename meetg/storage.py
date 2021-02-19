import time

import pymongo

import settings
from meetg.api_types import (
    ApiType, ChatApiType, MessageApiType, UpdateApiType, UserApiType,
)
from meetg.utils import get_unixtime_before_now, import_string
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

    def update(self, query, update):
        raise NotImplementedError

    def update_one(self, query, update):
        raise NotImplementedError

    def count(self, query=None):
        raise NotImplementedError

    def find(self, query=None):
        raise NotImplementedError

    def find_one(self, query=None):
        raise NotImplementedError

    def delete(self, query):
        raise NotImplementedError

    def delete_one(self, query):
        raise NotImplementedError

    def drop(self):
        raise NotImplementedError


class MongoStorage(AbstractStorage):
    """
    Wrapper for MongoDB collection methods. It's some kind of an ORM.
    The idea is that another potential storage, e.g. PostgreStorage,
    have to implement the same methods, allowing the same args to them.
    But I'm not sure it will be handful. So methods and args may change in the future.
    """
    def __init__(self, db_name, table_name, host='localhost', port=27017):
        super().__init__(db_name, table_name, host, port)
        self.client = pymongo.MongoClient(host=host, port=port)
        self.db = getattr(self.client, db_name)
        self.table = getattr(self.db, table_name)

    def create(self, entry):
        return self.table.insert_one(entry)

    def update(self, query, new_data):
        return self.table.update_many(query, {'$set': new_data})

    def update_one(self, query, new_data):
        return self.table.update_one(query, {'$set': new_data})

    def count(self, query=None):
        return self.table.count_documents(query or {})

    def find(self, query=None):
        return self.table.find(query)

    def find_one(self, query=None):
        return self.table.find_one(query)

    def delete(self, query):
        return self.table.delete_many(query)

    def delete_one(self, query):
        return self.table.delete_one(query)

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

    def _log_update(self, data: dict):
        logger.info('Storage: %s updated', self.name)

    def create(self, data: dict):
        data = self._validate(data)
        result = None
        if data:
            data['meetg_created_at'] = time.time()
            data['meetg_modified_at'] = None
            result = self._storage.create(data)
            self._log_create(data)
        return result

    def find(self, query=None):
        found = self._storage.find(query)
        return found

    def find_one(self, query=None):
        found = self._storage.find_one(query)
        return found

    def update(self, query, new_data):
        new_data = self._validate(new_data)
        new_data['meetg_modified_at'] = time.time()
        updated = self._storage.update(query, new_data)
        return updated

    def update_one(self, query, new_data):
        new_data = self._validate(new_data)
        new_data['meetg_modified_at'] = time.time()
        updated = self._storage.update_one(query, new_data)
        self._log_update(query)
        return updated

    def count(self, query=None):
        counted = self._storage.count(query)
        return counted

    def _get_created_for_day_query(self):
        query = {
            'meetg_created_at': {
                '$lt': time.time(),
                '$gte': get_unixtime_before_now(24),
            },
        }
        return query

    def get_day_report(self):
        query = self._get_created_for_day_query()
        count = self.count(query)
        return f'stored {count} new {self.name_lower}s'


class ApiTypeModel(BaseDefaultModel):
    """Base model class for objects related to Bot API"""

    def _log_create(self, data: dict):
        id_field = self.api_type.id_field
        if id_field in data:
            logger.info('Storage: %s %s created', self.name, data[id_field])
        else:
            logger.info('Storage: %s created', self.name)

    def _log_update(self, data: dict):
        id_field = self.api_type.id_field
        if id_field in data:
            logger.info('Storage: %s %s updated', self.name, data[id_field])
        else:
            logger.info('Storage: %s updated', self.name)

    def get_ptb_obj(self, update_obj):
        raise NotImplementedError

    def get_query(self, ptb_obj):
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
            query = self.get_query(ptb_obj)
            db_obj = self.find_one(query)
            if db_obj:
                if not self.is_equal(ptb_obj, db_obj):
                    self.update_one(query, ptb_obj.to_dict())
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

    def get_query(self, ptb_obj):
        query = {self.api_type.id_field: ptb_obj.update_id}
        return query


class DefaultMessageModel(ApiTypeModel):
    api_type = MessageApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_message
        return ptb_obj

    def get_query(self, ptb_obj):
        query = {self.api_type.id_field: ptb_obj.message_id, 'chat.id': ptb_obj.chat.id}
        return query


class DefaultUserModel(ApiTypeModel):
    api_type = UserApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_user
        return ptb_obj

    def get_query(self, ptb_obj):
        query = {self.api_type.id_field: ptb_obj.id}
        return query


class DefaultChatModel(ApiTypeModel):
    api_type = ChatApiType

    name = api_type.name
    fields = api_type.fields

    def get_ptb_obj(self, update_obj):
        ptb_obj = update_obj.effective_chat
        return ptb_obj

    def get_query(self, ptb_obj):
        query = {self.api_type.id_field: ptb_obj.id}
        return query


def get_model_classes():
    model_classes = [
        getattr(settings, k) for k in dir(settings)
        if k.endswith('_model_class')
    ]
    return model_classes


def mongo_get_first(cursor):
    """Return first item in the cursor"""
    return [item for item in cursor.limit(1)][0]


def mongo_get_last(cursor):
    """Return last item in the cursor"""
    return [item for item in cursor][-1]
