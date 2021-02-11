import os
import sys
import unittest

import settings
from meetg.utils import import_string


KNOWN_ARGS = ('run', 'test')


def run_bot(bot_path):
    Bot = import_string(bot_path)
    Bot().run()


def run_tests(import_pathes, src_path):
    """Run tests by import_pathes, or, if not provided, run all the tests"""
    loader = unittest.loader.TestLoader()
    if import_pathes:
        suite = loader.loadTestsFromNames(import_pathes)
    else:
        suite = loader.discover(src_path)

    result = unittest.runner.TextTestRunner().run(suite)


def exec_args(argv, src_path):
    if len(argv) > 1 and argv[1] in KNOWN_ARGS:
        if argv[1] == 'run':
            run_bot(settings.bot_class)
        if argv[1] == 'test':
            run_tests(argv[2:], src_path)
    else:
        print('Available commands:', ', '.join(KNOWN_ARGS))
