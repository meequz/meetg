import os
import sys
import unittest

import settings
from meetg.utils import import_string


KNOWN_ARGS = ('run', 'test')


def run():
    Bot = import_string(settings.bot_class)
    Bot().run()


def test(src_path):
    suite = unittest.loader.TestLoader().discover(src_path)
    result = unittest.runner.TextTestRunner().run(suite)


def exec_args(argv, src_path):
    if len(argv) > 1 and argv[1] in KNOWN_ARGS:
        if argv[1] == 'run':
            run()
        if argv[1] == 'test':
            test(src_path)
    else:
        print('Available commands:', ', '.join(KNOWN_ARGS))
