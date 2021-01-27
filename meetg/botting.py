import datetime, time

import telegram
import pytz
from telegram.ext import Handler, Updater

import settings
from meetg.api_methods import api_method_classes
from meetg.loging import get_logger
from meetg.storage import get_model_classes
from meetg.testing import UpdaterMock
from meetg.update_factories import (
    MessageUpdateFactory
)
from meetg.utils import import_string


logger = get_logger()


class BaseBot:
    """Common Telegram bot logic"""

    def __init__(self, mock=False):
        self._is_mock = mock
        self._init_updater()
        self._init_models(test=mock)
        self._init_handlers()
        self._init_jobs()

    def _init_updater(self):
        updater_class = UpdaterMock if self._is_mock else Updater
        self.updater = updater_class(settings.tg_api_token, use_context=True)
        self._tgbot = self.updater.bot
        self.username = self.updater.bot.get_me().username

    def _init_handlers(self):
        save_handler = SaveOnUpdateHandler(self._models)
        self._handlers = (save_handler,) + self.init_handlers()
        if not self._is_mock:
            for handler in self._handlers:
                self.updater.dispatcher.add_handler(handler)

    def init_handlers(self):
        """Intended to be redefined in your bot class"""
        logger.warning('No handlers found')
        return ()

    def init_jobs(self):
        """Intended to be redefined in your bot class"""
        pass

    def _init_jobs(self):
        """Set default jobs to self.updater.job_queue before self.init_jobs()"""
        stats_dt = datetime.time(tzinfo=pytz.timezone('UTC'))  # 00:00 UTC
        self.updater.job_queue.run_daily(self.job_report_stats, stats_dt)
        self.init_jobs()

    def _init_models(self, test=False):
        """Read model classes from settings, import and add them to self"""
        self._models = []
        for model_class in get_model_classes():
            model = import_string(model_class)(test=test)
            setattr(self, f'{model.name_lower}_model', model)
            self._models.append(model)

    def _mock_process_update(self, update_obj):
        """Simulation of telegram.ext.dispatcher.Dispatcher.process_update()"""
        for handler in self._handlers:
            check = handler.check_update(update_obj)
            if check not in (None, False):
                return handler.callback(update_obj, None)

    def job_report_stats(self, context):
        """Report bots stats daily"""
        if settings.stats_to:
            reports = ''.join([m.get_day_report() for m in self._models])
            text = f'@{self.username} for the last 24 hours:\n- {reports}'
            self.send_messages(settings.stats_to, text)

    def run(self):
        self.updater.start_polling()
        logger.info('%s started', self.username)
        self.updater.idle()

    def send_messages(self, chat_ids, text, reply_to=None, markup=None, html=None, preview=False):
        """Shortcut to replace multiple send_message API calls"""
        for chat_id in chat_ids:
            self.send_message(
                chat_id, text, reply_to=reply_to, markup=markup, html=html, preview=preview,
            )
        logger.info('Broadcasted message: %s', repr(text[:79]))

    def receive_message(self, text, **kwargs):
        """
        For using in tests.
        Simulates receiving Update with 'message' by the bot
        """
        factory = MessageUpdateFactory(self)
        update_obj = factory.create(text, **kwargs)
        return self._mock_process_update(update_obj)

    def __getattr__(self, name):
        """
        Find API method class by the name, create it,
        and return its easy_call method
        """
        method_class = api_method_classes.get(name)
        if method_class:
            method = method_class(self._tgbot, self._is_mock)
            self.last_method = method
            return method.easy_call


class SaveOnUpdateHandler(Handler):
    """
    Fake handler which handles no updates,
    but saves info from each Update for update-related models,
    if they are enabled
    """
    def __init__(self, models):
        super().__init__(lambda: None)
        # leave only enabled update-related models
        self.models = []
        for model in models:
            if model.related_to_update and model.save_fields:
                self.models.append(model)

    def check_update(self, update_obj):
        """The method triggers by PTB on each received update"""
        self.save(update_obj)

    def save(self, update_obj):
        """Save all the fields specified in enabled models"""
        for model in self.models:
            model.create_from_update_obj(update_obj)
