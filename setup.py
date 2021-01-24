#!/usr/bin/env python3
from setuptools import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    name='meetg',
    version='0.6',
    packages=['meetg'],
    scripts=['bin/meetg-admin'],
    description='Framework for creating Telegram bots',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/meequz/meetg',
    author='Mikhail Varantsou',
    license='LGPL-3.0',
    author_email='meequz@gmail.com',
    install_requires=['parameterized', 'python-telegram-bot', 'pymongo', 'pytz'],
    keywords='telegram bot framework',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.5',
)
