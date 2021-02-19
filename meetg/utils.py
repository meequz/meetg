import random, string, time
from collections import namedtuple
from importlib import import_module
from io import BytesIO

from PIL import Image
from telegram.messageentity import MessageEntity


def generate_random_string(length=22):
    population = string.ascii_letters + string.digits
    choices = random.choices(population, k=length)
    random_string = ''.join(choices)
    return random_string


def message_contain(msg, words):
    msg_words = msg.lower().split()
    for msg_word in msg_words:
        for word in words:
            if msg_word.startswith(word):
                return True


def message_starts(msg, words):
    msg = msg.lower()
    for word in words:
        if msg.startswith(word):
            return True


def frange(start, stop=None, step=None):
    while stop > start:
        yield start
        start += step


def get_current_unixtime():
    return time.time()


def import_string(dotted_path):
    module_path, class_name = dotted_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name)


def dict_to_obj(name, dictionary: dict):
    return namedtuple(name, dictionary.keys())(*dictionary.values())


def parse_entities(string):
    """
    In real world, Telegram server does it.
    But for testing we may automatically create them
    to not create in tests each time.
    """
    entities = []
    if string.startswith('/'):
        entity = MessageEntity(
            type=MessageEntity.BOT_COMMAND,
            offset=0,
            length=len(string.split()[0]),
        )
        entities.append(entity)
    return entities


def get_unixtime_before_now(hours: int):
    before = time.time() - hours * 60 * 60
    return before


def get_update_type(update_obj):
    for key in update_obj.to_dict():
        if key != 'update_id':
            return key


def get_1px_image():
    file = BytesIO()
    image = Image.new('1', size=(1, 1))
    image.save(file, 'png')
    file.seek(0)
    return file
