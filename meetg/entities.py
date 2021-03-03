import re

from telegram.messageentity import MessageEntity


regexps = {
    MessageEntity.EMAIL: '()(?P<entity>[\w\.-]+@[\w\.-]+\.\w+)',
    MessageEntity.BOT_COMMAND: '(^|\s)(?P<entity>/\w+)',
    MessageEntity.HASHTAG: '()(?P<entity>#\w*[a-zA-Z]\w*)',  # TODO: fix for non-latin
    MessageEntity.MENTION: '(^|\s)(?P<entity>@\w+)',
    MessageEntity.PHONE_NUMBER: '()(?P<entity>\+\d{11,12})(\D|$)',
    MessageEntity.URL: (
        '(^|\s)(?P<entity>([a-zA-Z]{2,10}\:\/\/)??[a-zA-Z0-9\.\/\?\:\-_=#]+\.'
        '([a-zA-Z]){2,10}([a-zA-Z0-9\.\&\/\?\:\-_=#]*))($|\s)'
    )
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
            if match.group('entity').strip():
                start, end = match.span(2)
                entity = MessageEntity(type=entity_type, offset=start, length=end-start)
                entities.append(entity)
    return entities
