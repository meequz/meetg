import datetime, time

import telegram
import pytz
from telegram.ext import Handler, Updater

import settings
from meetg.loging import get_logger
from meetg.storage import get_model_classes
from meetg.testing import UpdaterMock, create_update_obj
from meetg.utils import extract_by_dotted_path, import_string


logger = get_logger()


class BaseBot:
    """Common Telegram bot logic"""
    save_users = True
    save_chats = True
    save_messages = False

    def __init__(self, mock=False):
        self._is_mock = mock
        self._init_tgbot()
        self._init_models(test=mock)
        self._init_handlers()
        self.set_jobs()

    def _init_tgbot(self):
        updater_class = UpdaterMock if self._is_mock else Updater
        self.updater = updater_class(settings.tg_api_token, use_context=True)
        self._tgbot = self.updater.bot
        self._username = self.updater.bot.get_me().username

    def _init_handlers(self):
        initial_handler = InitialHandler(self.update_model)
        self._handlers = (initial_handler,) + self.set_handlers()
        if not self._is_mock:
            for handler in self._handlers:
                self.updater.dispatcher.add_handler(handler)

    def set_handlers(self):
        """
        This method intended to be redefined in your bot class
        """
        logger.warning('No handlers found')
        return ()

    def set_jobs(self):
        """
        Set default jobs to self.updater.job_queue.
        May be redefined in a subclass, but don't forget to call super() then
        """
        stats_dt = datetime.time(tzinfo=pytz.timezone('UTC'))  # 00:00 UTC
        self.updater.job_queue.run_daily(self.job_stats, stats_dt)

    def _init_models(self, test=False):
        """Read model classes from settings, import and add them to self"""
        for model_class in get_model_classes():
            model = import_string(model_class)(test=test)
            setattr(self, f'{model.name_lower}_model', model)

    def _mock_process_update(self, update_obj):
        """Simulation of telegram.ext.dispatcher.Dispatcher.process_update()"""
        for handler in self._handlers:
            check = handler.check_update(update_obj)
            if check not in (None, False):
                return handler.callback(update_obj, None)

    def test_send(
            self, message_text: str, user_first_name=None, chat_title=None, chat_type='private',
        ):
        """
        Method to use in auto tests.
        Simulate sending messages to the bot
        """
        kwargs = {}
        if user_first_name is not None:
            kwargs['user_first_name'] = user_first_name
        update_obj = create_update_obj(
            message_text=message_text, chat_type=chat_type, chat_title=chat_title, bot=self._tgbot,
            **kwargs,
        )
        return self._mock_process_update(update_obj)

    def job_stats(self, context):
        """Report bots stats"""
        if not settings.stats_to:
            return

        reports = '\n- '.join([
            self.update_model.get_count_report(),
        ])
        text = f'@{self._username} for the last 24 hours:\n- {reports}'
        self.broadcast(settings.stats_to, text)

    def run(self):
        self.updater.start_polling()
        logger.info('%s started', self._username)
        self.updater.idle()

    def extract(self, update_obj, *args):
        """
        Extract data from update_obj according to args
        """
        update_dict = update_obj.to_dict()
        extracted = [extract_by_dotted_path(update_dict, path) for path in args]
        if len(extracted) == 1:
            extracted = extracted[0]
        return extracted

    def _log_api_call(self, method_name, kwargs):
        chat_id = kwargs.get('chat_id')
        message_id = kwargs.get('message_id')
        text = repr(kwargs.get('text', ''))

        if method_name == 'send_message':
            logger.info('Send message to chat %s, text length %s', chat_id, len(text))
        elif method_name == 'edit_message_text':
            logger.info('Edit message %s in chat %s', message_id, chat_id)
        elif method_name == 'delete_message':
            logger.info('Delete message %s in chat %s', message_id, chat_id)
        else:
            raise NotImplementedError

    def _mock_remember(self, method_name, method_args):
        """
        If the object of the class is a mock,
        then just remember the API method and the args going to be used
        """
        self.api_method_called = method_name
        self.api_args_used = method_args
        if 'text' in method_args:
            self.api_text_sent = method_args.get('text', '')
        return None, None

    def call_bot_api(self, method_name: str, **kwargs):
        """
        Retries and handling network and load issues
        """
        if self._is_mock:
            return self._mock_remember(method_name, kwargs)

        to_attempt = 5
        success = False
        self._log_api_call(method_name, kwargs)
        method = getattr(self._tgbot, method_name)
        chat_id = kwargs.pop('chat_id', None)

        while to_attempt > 0:
            try:
                resp = method(chat_id=chat_id, **kwargs)
                success = True
                to_attempt = 0
            except telegram.error.NetworkError as exc:
                prefix = 'Network error: '
                if 'are exactly the same as' in exc.message:
                    logger.error(prefix + '"%s". It\'s ok, nothing to do here', exc.message)
                    success = True
                    to_attempt = 0
                elif "Can't parse entities" in exc.message:
                    logger.error(prefix + '"%s". Retrying is pointless', exc.message)
                    to_attempt = 0
                else:
                    logger.error(prefix + '"%s". Waiting 2 seconds then retry', exc.message)
                    to_attempt -= 1
                    time.sleep(2)
                resp = exc.message
            except telegram.error.TimedOut as exc:
                logger.error('Timed Out. Retrying')
                resp = exc.message
                to_attempt -= 1
            except telegram.error.RetryAfter as exc:
                logger.error('It is asked to retry after %s seconds. Doing', exc.retry_after)
                resp = exc.message
                to_attempt -= 2
                time.sleep(exc.retry_after + 1)
            except telegram.error.ChatMigrated as exc:
                logger.error('ChatMigrated error: "%s". Retrying with new chat id', exc)
                resp = exc.message
                chat_id = exc.new_chat_id
                to_attempt -= 1
            except (telegram.error.Unauthorized, telegram.error.BadRequest) as exc:
                logger.error('Error: "%s". Retrying', exc)
                resp = exc.message
                to_attempt -= 2
        logger.debug('Success' if success else 'Fail')
        return success, resp

    def broadcast(self, chat_ids, text, html=False):
        for chat_id in chat_ids:
            self.send_message(chat_id, text, html=html)
        logger.info('Broadcasted: %s', repr(text[:79]))

    def send_message(self, chat_id, text, msg_id=None, markup=None, html=None, preview=False):
        parse_mode = telegram.ParseMode.HTML if html else None
        success, resp = self.call_bot_api(
            'send_message',
            chat_id=chat_id, text=text, reply_to_message_id=msg_id, reply_markup=markup,
            parse_mode=parse_mode, disable_web_page_preview=not preview,
        )
        return success, resp

    def edit_msg_text(self, chat_id, text, msg_id, preview=False):
        success, resp = self.call_bot_api(
            'edit_message_text',
            text=text, chat_id=chat_id, message_id=msg_id, disable_web_page_preview=not preview,
        )
        return success, resp

    def delete_msg(self, chat_id, msg_id):
        success, resp = self.call_bot_api(
            'delete_message',
            chat_id=chat_id, message_id=msg_id,
        )
        return success, resp


class InitialHandler(Handler):
    """
    Fake handler which handles no updates,
    but performs actions on every update,
    if they are required, e.g. saving in database
    """
    def __init__(self, update_model, *args):
        super().__init__(lambda: None)
        self.update_model = update_model

    def check_update(self, update_obj):
        self.update_model.create(update_obj.to_dict())
