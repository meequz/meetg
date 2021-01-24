import logging


tg_api_token = ''

db_name = ''
db_name_test = ''

db_host = 'localhost'
db_port = 27017

storage_class = 'meetg.storage.MongoStorage'
update_model_class = 'meetg.storage.DefaultUpdateModel'

bot_class = 'bot.MyBot'

log_path = 'log.txt'
log_level = logging.INFO

stats_to = ()
