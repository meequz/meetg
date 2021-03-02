import random, string, time
from collections import namedtuple
from importlib import import_module
from io import BytesIO

from PIL import Image


def generate_random_string(length=22):
    population = string.ascii_letters + string.digits
    choices = random.choices(population, k=length)
    random_string = ''.join(choices)
    return random_string


def message_contains(msg, words):
    msg_words = msg.lower().split()
    for msg_word in msg_words:
        for word in words:
            if msg_word.startswith(word):
                return True


def message_startswith(msg, words):
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


def get_unixtime_before_now(hours: int):
    before = time.time() - hours * 60 * 60
    return before


def get_update_type(update_obj):
    for key in update_obj.to_dict():
        if key != 'update_id':
            return key


def true_only(collection):
    collection_type = type(collection)
    return collection_type(item for item in collection if item)
