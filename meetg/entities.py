import re
from telegram.messageentity import MessageEntity


regexps = {
    MessageEntity.EMAIL: '[\w\.-]+@[\w\.-]+\.\w+',
    MessageEntity.BOT_COMMAND: '/\w+',
    
    # TODO
    # MessageEntity.HASHTAG: '',
    # MessageEntity.MENTION: '',
    # MessageEntity.PHONE_NUMBER: '',
    # MessageEntity.URL: '',
}


def parse_entities(string, mode=None):
    """
    In real world, Telegram server does it.
    But for testing we may automatically create them
    to not create in tests each time.
    """
    entities = []
    for entity_type, regexp in regexps.items():
        for match in re.finditer(regexp, string):
            start, end = match.span()
            entity = MessageEntity(type=entity_type, offset=start, length=end-start)
            entities.append(entity)
    return entities
