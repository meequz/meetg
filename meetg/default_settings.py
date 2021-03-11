import logging


tg_api_token = ''

db_name = ''
db_name_test = ''

db_host = 'localhost'
db_port = 27017

storage_class = 'meetg.storage.MongoStorage'
Update_model = 'meetg.storage.DefaultUpdateModel'
Message_model = 'meetg.storage.DefaultMessageModel'
User_model = 'meetg.storage.DefaultUserModel'
Chat_model = 'meetg.storage.DefaultChatModel'

bot_class = 'meetg.botting.BaseBot'

api_attempts = 5
network_error_wait = 2

log_path = 'log.txt'
log_level = logging.INFO

stats_to = ()


is_test = False
