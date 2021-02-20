#!/usr/bin/env python3
import os, sys
from setuptools import Command, setup


with open('README.md') as f:
    long_description = f.read()


class TestCommand(Command):
    description = 'Run project tests'
    user_options = [
        ('suites=', 's', 'Specify the test suites to run, separated by comma'),
    ]

    def initialize_options(self):
        self.suites = None

    def finalize_options(self):
        pass

    def run(self):
        from meetg.manage import run_tests
        suites = self.suites.split(',') if self.suites else []
        src_path = os.path.dirname(os.path.abspath(__file__))
        run_tests(suites, src_path)


setup(
    name='meetg',
    version='0.9.2',
    packages=['meetg'],
    scripts=['bin/meetg-admin'],
    description='Framework for creating Telegram bots',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/meequz/meetg',
    author='Mikhail Varantsou',
    license='LGPL-3.0',
    author_email='meequz@gmail.com',
    install_requires=['parameterized', 'pillow', 'python-telegram-bot', 'pymongo', 'pytz'],
    keywords='telegram bot framework',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    cmdclass={
        'test': TestCommand,
    },
)
