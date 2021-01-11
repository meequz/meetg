import time

import telegram
from telegram.ext import Updater

import settings
from meetg.utils import import_string
from meetg.loging import get_logger
from meetg.testing import UpdaterBotMock, create_update_obj


logger = get_logger()


class BaseBot:
    """Common Telegram bot logic"""
    save_users = True
    save_chats = True
    save_messages = False

    def __init__(self, mock=False):
        self._is_mock = mock
        if mock:
            self._tgbot = UpdaterBotMock()
            self._tgbot_username = self._tgbot.username
        else:
            self._updater = Updater(settings.tg_api_token, use_context=True)
            self._tgbot = self._updater.bot
            self._tgbot_username = self._updater.bot.get_me().username
        self._init_handlers()
        self._init_models(test=mock)

    def _init_handlers(self):
        self._handlers = self.set_handlers()
        if not self._is_mock:
            for handler in self._handlers:
                self._updater.dispatcher.add_handler(handler)

    def set_handlers(self):
        logger.warning('No handlers found')
        return ()

    def _init_models(self, test=False):
        self.user_model = import_string(settings.user_model_class)(test=test)
        self.chat_model = import_string(settings.chat_model_class)(test=test)
        self.message_model = import_string(settings.message_model_class)(test=test)

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

    def run(self):
        self._updater.start_polling()
        logger.info('%s started', self._tgbot_username)
        self._updater.idle()

    def _save(self, update_obj):
        """
        Save all the object have to be saved according to bot attrs in DB
        """
        if self.save_users:
            user = update_obj.message.from_user
            self._save_obj(user.id, user, self.user_model)
        if self.save_chats:
            chat = update_obj.message.chat
            self._save_obj(chat.id, chat, self.chat_model)
        if self.save_messages:
            message = update_obj.message
            self._save_obj(message.message_id, message, self.message_model)

    def _save_obj(self, obj_id, obj, model):
        """
        Save an object in DB
        """
        db_obj = model.find_one(obj_id)
        if db_obj:
            model.update_from_obj(obj)
        else:
            model.create_from_obj(obj)

    def extract(self, update_obj):
        """
        Extract commonly used info from update_obj,
        save users in db if they're new, log new message
        """
        chat_id = update_obj.message.chat.id
        msg_id = update_obj.message.message_id
        user = update_obj.message.from_user
        text = update_obj.message.text
        self._save(update_obj)

        contact = update_obj.message.contact
        location = update_obj.message.location

        if contact:
            logger.info('Received contact from chat %s', chat_id)
        elif location:
            logger.info('Received location from chat %s', chat_id)
        else:
            logger.info('Received message from chat %s, text length %s', chat_id, len(text or ''))
        return chat_id, msg_id, user, text

    def _log_api_call(self, method_name, kwargs):
        chat_id = kwargs.get('chat_id')
        message_id = kwargs.get('message_id')
        text = repr(kwargs.get('text', ''))

        if method_name == 'send_message':
            logger.info('Send answer to chat %s, text length %s', chat_id, len(text))
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

    def broadcast(self, chat_ids, body, html=False):
        for chat_id in chat_ids:
            self.send_msg(chat_id, body, html=html)
        logger.info('Broadcasted: %s', body[:79])

    def send_msg(self, chat_id, body, msg_id=None, markup=None, html=None, preview=False):
        parse_mode = telegram.ParseMode.HTML if html else None
        success, resp = self.call_bot_api(
            'send_message',
            chat_id=chat_id, text=body, reply_to_message_id=msg_id, reply_markup=markup,
            parse_mode=parse_mode, disable_web_page_preview=not preview,
        )
        return success, resp

    def edit_msg_text(self, chat_id, body, msg_id, preview=False):
        success, resp = self.call_bot_api(
            'edit_message_text',
            text=body, chat_id=chat_id, message_id=msg_id, disable_web_page_preview=not preview,
        )
        return success, resp

    def delete_msg(self, chat_id, msg_id):
        success, resp = self.call_bot_api(
            'delete_message',
            chat_id=chat_id, message_id=msg_id,
        )
        return success, resp
