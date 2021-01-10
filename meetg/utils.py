import random, string, time
from collections import namedtuple
from importlib import import_module


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
    return int(time.time())


def import_string(dotted_path):
    module_path, class_name = dotted_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name)


def dict_to_obj(name, dictionary: dict):
    return namedtuple(name, dictionary.keys())(*dictionary.values())
