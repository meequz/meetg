import time

import telegram

import settings
from meetg.loging import get_logger


logger = get_logger()


class ApiMethod:

    def __init__(self, tgbot, is_mock=False):
        self.tgbot = tgbot
        self.is_mock = is_mock
        self.args = None

    def easy_call(self, **kwargs):
        """Call the method by simplified params"""
        raise NotImplementedError

    def log(self, kwargs):
        raise NotImplementedError

    def call(self, **kwargs):
        """
        Call the method by the exact Telegram API params,
        by keyword arguments only, to easily validate them
        """
        self.args = kwargs.copy()
        kwargs = self._validate(kwargs)
        if self.is_mock:
            success, response = None, None
        else:
            success, response = self._call(kwargs)
        if success:
            self.log(self.args)
        return success, response

    def __str__(self):
        if self.args:
            return f'{self.name}: {self.args}'
        else:
            return f'{self.name}: no args'

    def _call(self, kwargs):
        """
        Retries, handling network and load issues
        """
        to_attempt = settings.api_attempts
        success, response = False, None
        tgbot_method = getattr(self.tgbot, self.name)

        while to_attempt > 0:
            try:
                response = tgbot_method(**kwargs)
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
                elif "Message to forward not found" in exc.message:
                    logger.error(prefix + '"%s". Retrying is pointless', exc.message)
                    to_attempt = 0
                else:
                    logger.error(
                        prefix + '"%s". Waiting %s seconds then retry',
                        settings.network_error_wait, exc.message,
                    )
                    to_attempt -= 1
                    time.sleep(settings.network_error_wait)
                response = exc.message
            except telegram.error.TimedOut as exc:
                logger.error('Timed Out. Retrying')
                response = exc.message
                to_attempt -= 1
            except telegram.error.RetryAfter as exc:
                logger.error('It is asked to retry after %s seconds. Doing', exc.retry_after)
                response = exc.message
                to_attempt -= 2
                time.sleep(exc.retry_after + 1)
            except telegram.error.ChatMigrated as exc:
                logger.error('ChatMigrated error: "%s". Retrying with new chat id', exc)
                response = exc.message
                kwargs['chat_id'] = exc.new_chat_id
                to_attempt -= 1
            except (telegram.error.Unauthorized, telegram.error.BadRequest) as exc:
                logger.error('Error: "%s". Retrying', exc)
                response = exc.message
                to_attempt -= 2
        logger.debug('Success' if success else 'Fail')
        return success, response

    def _validate(self, data):
        validated = {}
        for key in data:
            if key in self.parameters:
                validated[key] = data[key]
            else:
                logger.warning('Method %s doesn\'t accept arg %s', self.name, key)
        return validated


class SendMessageMethod(ApiMethod):
    name = 'send_message'
    parameters = (
        # required
        'chat_id', 'text',
        # optional
        'parse_mode', 'entities', 'disable_web_page_preview', 'disable_notification',
        'reply_to_message_id', 'allow_sending_without_reply', 'reply_markup', 
    )

    def easy_call(self, chat_id, text, reply_to=None, markup=None, html=None, preview=False):
        parse_mode = telegram.ParseMode.HTML if html else None
        success, response = self.call(
            chat_id=chat_id, text=text, reply_to_message_id=reply_to, reply_markup=markup,
            parse_mode=parse_mode, disable_web_page_preview=not preview,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        text = repr(kwargs.get('text', ''))
        logger.info('Send message to chat %s, text length %s', chat_id, len(text))


class EditMessageTextMethod(ApiMethod):
    name ='edit_message_text'
    parameters = (
        # required
        'text',
        # optional
        'chat_id', 'message_id', 'inline_message_id', 'parse_mode', 'entities',
        'disable_web_page_preview', 'reply_markup',
    )
    def easy_call(self, text, chat_id, message_id, preview=False):
        success, response = self.call(
            text=text, chat_id=chat_id, message_id=message_id,
            disable_web_page_preview=not preview,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        message_id = kwargs.get('message_id')
        logger.info('Edit message %s in chat %s', message_id, chat_id)


class DeleteMessageMethod(ApiMethod):
    name = 'delete_message'
    parameters = (
        # required
        'chat_id', 'message_id',
    )
    def easy_call(self, chat_id, message_id):
        success, response = self.call(
            chat_id=chat_id, message_id=message_id,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        message_id = kwargs.get('message_id')
        logger.info('Delete message %s in chat %s', message_id, chat_id)


class ForwardMessageMethod(ApiMethod):
    name = 'forward_message'
    parameters = (
        # required
        'chat_id', 'from_chat_id', 'message_id',
        # optional
        'disable_notification',
    )
    def easy_call(self, chat_id, from_chat_id, message_id, notify=True):
        success, response = self.call(
            chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id,
            disable_notification=not notify,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        from_chat_id = kwargs.get('from_chat_id')
        message_id = kwargs.get('message_id')
        logger.info(
            'Forward message %s from chat %s to chat %s',
            message_id, from_chat_id, chat_id,
        )


class SendPhotoMethod(ApiMethod):
    name = 'send_photo'
    parameters = (
        # required
        'chat_id', 'photo',
        # optional
        'caption', 'parse_mode', 'caption_entities', 'disable_notification', 'reply_to_message_id',
        'allow_sending_without_reply', 'reply_markup',
    )

    def easy_call(self, chat_id, photo, caption=None, reply_to=None, markup=None, html=None):
        parse_mode = telegram.ParseMode.HTML if html else None
        success, response = self.call(
            chat_id=chat_id, photo=photo, caption=caption, reply_to_message_id=reply_to,
            reply_markup=markup, parse_mode=parse_mode,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send photo to chat %s', chat_id)


class SendDocumentMethod(ApiMethod):
    name = 'send_document'
    parameters = (
        # required
        'chat_id', 'document',
        # optional
        'thumb', 'caption', 'parse_mode', 'caption_entities', 'disable_content_type_detection',
        'disable_notification', 'reply_to_message_id', 'allow_sending_without_reply',
        'reply_markup',
    )

    def easy_call(
            self, chat_id, document, thumb=None, caption=None, reply_to=None, markup=None,
            html=None,
        ):
        parse_mode = telegram.ParseMode.HTML if html else None
        success, response = self.call(
            chat_id=chat_id, document=document, thumb=thumb, caption=caption,
            reply_to_message_id=reply_to, reply_markup=markup, parse_mode=parse_mode,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send document to chat %s', chat_id)


api_method_classes = {
    'send_message': SendMessageMethod,
    'send_photo': SendPhotoMethod,
    'send_document': SendDocumentMethod,
    'edit_message_text': EditMessageTextMethod,
    'delete_message': DeleteMessageMethod,
    'forward_message': ForwardMessageMethod,
}
