import pymongo

import settings
from meetg.utils import serialize_user
from meetg.loging import get_logger


logger = get_logger()


class MongoStorage(object):
    """Wrapper for MongoDB collection methods"""

    def __init__(self, db_name, collection_name):
        self.client = pymongo.MongoClient()
        self.db_name = db_name
        self.collection_name = collection_name
        self.db = getattr(self.client, db_name)
        self.collection = getattr(self.db, collection_name)

    def create(self, entry):
        return self.collection.insert_one(entry)

    def update(self, pattern, update):
        return self.collection.update_many(pattern, update)

    def update_one(self, pattern, update):
        return self.collection.update_one(pattern, update)

    def count(self, pattern=None):
        return self.collection.count(pattern)

    def find(self, pattern=None):
        return self.collection.find(pattern)

    def find_one(self, pattern=None):
        return self.collection.find_one(pattern)

    def delete(self, pattern):
        return self.collection.delete_many(pattern)

    def delete_one(self, pattern):
        return self.collection.delete_one(pattern)

    def drop(self):
        return self.db.drop_collection(self.collection_name)


class Database:
    """High-level methods to read/write data"""

    _user_fields = (
        'username', 'first_name', 'last_name', 'is_bot', 'language_code', 'phone_number', 'lat',
        'lon', 'map_link', 'notification_msg_id',
    )

    def __init__(self):
        db_name = settings.mongo_db_name
        user_collection_name = settings.mongo_user_collection_name
        self._user_st = MongoStorage(db_name, user_collection_name)

    def drop_all(self):
        self._user_st.drop()

    def create_user(
            self, chat_id, username=None, first_name=None, last_name=None, is_bot=None,
            language_code=None, phone_number=None, lat=None, lon=None, map_link=None,
            notification_msg_id=None,
        ):
        user_data = {
            'chat_id': chat_id, 'username': username, 'first_name': first_name,
            'last_name': last_name, 'is_bot': is_bot, 'language_code': language_code,
            'phone_number': phone_number, 'lat': lat, 'lon': lon, 'map_link': map_link,
            'notification_msg_id': notification_msg_id,
        }
        self._user_st.create(user_data)
        logger.info('User %s added to DB', chat_id)
        logger.debug('id %s is user %s', chat_id, serialize_user(user_data))
        return user_data

    def create_user_from_tg_user_obj(self, tg_user):
        user_data = {
            'chat_id': tg_user.id,
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
            'is_bot': tg_user.is_bot,
            'language_code': tg_user.language_code,
        }
        user = self.create_user(**user_data)
        return user

    def update_user(self, chat_id, **kwargs):
        # check kwargs are valid user fields
        new_data = {kwa: kwargs[kwa] for kwa in kwargs if kwa in self._user_fields}

        if new_data.get('lat') and new_data.get('lon'):
            new_data['map_link'] = (
                f"https://maps.google.com/maps?q={new_data['lat']},{new_data['lon']}"
            )

        result = self._user_st.update_one({'chat_id': chat_id}, {'$set': new_data})
        user = self.get_user(chat_id)
        logger.info('User %s updated in DB', chat_id)
        logger.debug('id %s is user %s', chat_id, serialize_user(user))
        return user

    def update_user_from_tg_user_obj(self, tg_user):
        chat_id = tg_user.id
        user_data = {
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
            'is_bot': tg_user.is_bot,
            'language_code': tg_user.language_code,
        }
        user = self.update_user(chat_id, **user_data)
        return user

    def get_user(self, chat_id):
        return self._user_st.find_one({'chat_id': chat_id})

    def get_users(self):
        return self._user_st.find()
