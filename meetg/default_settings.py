import logging


tg_api_token = ''

db_name = ''
db_name_test = ''

db_host = 'localhost'
db_port = 27017

storage_class = 'meetg.storage.MongoStorage'
update_model_class = 'meetg.storage.DefaultUpdateModel'
message_model_class = 'meetg.storage.DefaultMessageModel'
user_model_class = 'meetg.storage.DefaultUserModel'
chat_model_class = 'meetg.storage.DefaultChatModel'

bot_class = 'bot.MyBot'

api_attempts = 5
network_error_wait = 2

log_path = 'log.txt'
log_level = logging.INFO

stats_to = ()
