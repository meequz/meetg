import time

import telegram
from telegram.ext import Updater

import settings
from meetg.utils import serialize_user
from meetg.loging import get_logger


logger = get_logger()


class BaseBot:
    """Common Telegram bot logic"""

    def __init__(self, db):
        self._db = db
        self._updater = Updater(settings.tg_api_token, use_context=True)
        self._tgbot = self._updater.bot
        self._tgbot_username = self._updater.bot.get_me().username
        self._init_handlers()

    def _init_handlers(self):
        handlers = self.get_handlers()
        for handler in handlers:
            self._updater.dispatcher.add_handler(handler)

    def run(self):
        self._updater.start_polling()
        logger.info(f'{self._tgbot_username} started')
        self._updater.idle()

    def extract(self, update_obj):
        """Extract commonly used info from update_obj,
        save users in db if they're new, log new message
        """
        chat_id = update_obj.message.chat.id
        msg_id = update_obj.message.message_id
        user = self._db.get_user(chat_id)
        text = update_obj.message.text

        contact = update_obj.message.contact
        location = update_obj.message.location
        text_for_log = repr(text or '')
        tg_user_obj = update_obj.message.from_user

        if user:
            user = self._db.update_user_from_tg_user_obj(tg_user_obj)
        else:
            user = self._db.create_user_from_tg_user_obj(tg_user_obj)

        if contact:
            logger.info('Received contact from %s', chat_id)
            logger.debug(
                'id %s is user %s, contact is %s', chat_id, serialize_user(user),
                contact.phone_number,
            )
        elif location:
            logger.info('Received location from %s', chat_id)
            logger.debug(
                'id %s is user %s, location is %s', chat_id, serialize_user(user),
                location,
            )
        else:
            logger.info('Received message with len %s from %s', len(text or ''), chat_id)
            logger.debug(
                'id %s is user %s, message is: %s', chat_id, serialize_user(user),
                text_for_log[:119],
            )
        return chat_id, msg_id, user, text

    def _log_api_call(self, method_name, kwargs):
        chat_id = kwargs.get('chat_id')
        message_id = kwargs.get('message_id')
        text = repr(kwargs.get('text', ''))

        if method_name == 'send_message':
            logger.info('Sending message with len %s to %s', len(text), chat_id)
            logger.debug('Message: %s', text[:119])
        elif method_name == 'edit_message_text':
            logger.info('Editing message %s in chat %s', message_id, chat_id)
        elif method_name == 'delete_message':
            logger.info('Deleting message %s in chat %s', message_id, chat_id)
        else:
            raise NotImplementedError

    def _call_bot_api(self, method_name: str, **kwargs):
        """
        Here is retry logic and logic for dealing with network and load issues
        """
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
                if 'are exactly the same as' in exc.message:
                    logger.error('Network error: "%s". It\'s ok, nothing to do here', exc.message)
                    success = True
                    to_attempt = 0
                elif "Can't parse entities" in exc.message:
                    logger.error('Network error: "%s". Retrying is pointless', exc.message)
                    to_attempt = 0
                else:
                    logger.error(
                        'Network error: "%s". Waiting 2 seconds then retry', exc.message,
                    )
                    to_attempt -= 1
                    time.sleep(2)
                resp = exc.message
            except telegram.error.TimedOut as exc:
                logger.error('Timed Out. Retrying')
                resp = exc.message
                to_attempt -= 1
            except telegram.error.RetryAfter as exc:
                logger.error(
                    'Telegram says to wait and retry after %s seconds. Doing', exc.retry_after,
                )
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
        success, resp = self._call_bot_api(
            'send_message',
            chat_id=chat_id, text=body, reply_to_message_id=msg_id, reply_markup=markup,
            parse_mode=parse_mode, disable_web_page_preview=not preview,
        )
        return success, resp

    def edit_msg_text(self, chat_id, body, msg_id, preview=False):
        success, resp = self._call_bot_api(
            'edit_message_text',
            text=body, chat_id=chat_id, message_id=msg_id, disable_web_page_preview=not preview,
        )
        return success, resp

    def delete_msg(self, chat_id, msg_id):
        success, resp = self._call_bot_api(
            'delete_message',
            chat_id=chat_id, message_id=msg_id,
        )
        return success, resp
