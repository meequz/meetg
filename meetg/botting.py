import datetime, time
from collections import defaultdict

import telegram
import pytz
from telegram.ext import Handler, Updater

import settings
from meetg.api_methods import api_method_classes
from meetg.loging import get_logger
from meetg.stats import (
    DateCache, get_job_reports, get_update_reports, _SaveTimeJobQueueWrapper, service_cache,
)
from meetg.storage import ApiTypeModel, get_model_classes
from meetg.testing import UpdaterMock
from meetg.factories import MessageUpdateFactory
from meetg.utils import (
    get_current_unixtime, get_unixtime_before_now, get_update_type, import_string,
)


logger = get_logger()


class BaseBot:
    """Common Telegram bot logic"""

    def __init__(self, mock=False):
        self._is_mock = mock
        self._init_updater()
        self._init_models(test=mock)
        self._init_handlers()
        self._init_jobs()
        self.last_method = None

    def _init_updater(self):
        """Init PTB updater"""
        updater_class = UpdaterMock if self._is_mock else Updater
        self.updater = updater_class(settings.tg_api_token, use_context=True)
        self._tgbot = self.updater.bot
        self.username = self.updater.bot.get_me().username

    def _init_handlers(self):
        service_handler = _ServiceHandler(self._models)
        self._handlers = (service_handler,) + self.init_handlers()
        if not self._is_mock:
            for handler in self._handlers:
                self.updater.dispatcher.add_handler(handler)

    def init_handlers(self):
        """Intended to be redefined in your bot class"""
        logger.warning('No handlers found')
        return ()

    def init_jobs(self, job_queue):
        """Intended to be redefined in your bot class"""
        pass

    def _init_jobs(self):
        """Set default jobs to self.updater.job_queue before self.init_jobs()"""
        self._job_queue_wrapper = _SaveTimeJobQueueWrapper(self.updater.job_queue)
        stats_dt = datetime.time(tzinfo=pytz.timezone('UTC'))  # 00:00 UTC
        self._job_queue_wrapper.run_daily(self._job_report_stats, stats_dt)
        self.init_jobs(self._job_queue_wrapper)

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

    def _job_report_stats(self, context=None):
        """Report bots stats daily"""
        job_reports = get_job_reports()
        update_reports = get_update_reports()
        model_reports = [m.get_day_report() for m in self._models]

        prefix = f'@{self.username} for the last 24 hours:'
        lines = [prefix] + update_reports + model_reports + job_reports
        report = '\n- '.join(lines)

        logger.info(report)
        if settings.stats_to:
            self.send_messages(settings.stats_to, report)

    def run(self):
        self.updater.start_polling()
        logger.info('@%s started', self.username)
        self.updater.idle()

    def send_messages(self, chat_ids, text, reply_to=None, markup=None, html=None, preview=False):
        """Shortcut to replace multiple send_message API calls"""
        for chat_id in chat_ids:
            self.send_message(
                chat_id, text, reply_to=reply_to, markup=markup, html=html, preview=preview,
            )
        logger.info('Message broadcasted: %s', repr(text[:79]))

    def receive_message(self, text='', **kwargs):
        """
        Simulates receiving Update with 'message' by the bot in tests
        """
        factory = MessageUpdateFactory(self, 'message')
        update_obj = factory.create(text=text, **kwargs)
        return self._mock_process_update(update_obj)

    def receive_edited_message(self, text, chat_id, message_id, **kwargs):
        """
        Simulates receiving Update with 'edited_message' by the bot in tests
        """
        factory = MessageUpdateFactory(self, 'edited_message')
        update_obj = factory.create(text=text, chat__id=chat_id, message_id=message_id, **kwargs)
        return self._mock_process_update(update_obj)

    def __getattr__(self, attrname):
        """
        Find API method class by the name, instantiate it,
        remember in self.last_method and return generated method
        with its easy_call() result inside
        """
        method_class = api_method_classes.get(attrname)
        if method_class:
            method_obj = method_class(self._tgbot, self._is_mock)
            self.last_method = method_obj

            def _internal_call(*args, **kwargs):
                return method_obj.easy_call(*args, **kwargs)

            return _internal_call

        else:
            raise NameError(f'API method {attrname} not found')


class _ServiceHandler(Handler):
    """
    Fake handler which handles no updates,
    but saves info from each Update for update-related models,
    if they are enabled, and count stats
    """
    def __init__(self, models):
        super().__init__(lambda: None)
        self.gather_models(models)

    def gather_models(self, models):
        """Gather models related to Bot API, to save them later"""
        self.models = []
        for model in models:
            if isinstance(model, ApiTypeModel) and model.fields:
                self.models.append(model)

    def check_update(self, update_obj):
        """The method triggers by PTB on each received update"""
        self.save(update_obj)
        self.count(update_obj)

    def count(self, update_obj):
        """Count stats for a later report"""
        update_type = get_update_type(update_obj)
        service_cache['stats']['update'].init(DateCache)
        service_cache['stats']['update'][update_type].add()

    def save(self, update_obj):
        """Save all the fields specified in enabled models"""
        for model in self.models:
            model.save_from_update_obj(update_obj)
