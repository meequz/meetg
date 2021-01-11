import logging


tg_api_token = ''

db_name = ''
db_name_test = ''
user_table = 'users'
chat_table = 'chats'
message_table = 'messages'

db_host = 'localhost'
db_port = 27017
storage_class = 'meetg.storage.MongoStorage'

user_model_class = 'meetg.storage.DefaultUserModel'
chat_model_class = 'meetg.storage.DefaultChatModel'
message_model_class = 'meetg.storage.DefaultMessageModel'
model_classes = (user_model_class, chat_model_class, message_model_class)

bot_class = 'bot.MyBot'
db_class = 'meetg.storage.Database'

log_path = 'log.txt'
log_level = logging.INFO
