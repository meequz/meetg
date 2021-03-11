import time

import telegram

import settings
from meetg.loging import get_logger
from meetg.storage import db
from meetg.utils import get_current_unixtime


logger = get_logger()


class ApiMethod:

    def __init__(self, tgbot, raise_exception=None):
        self.tgbot = tgbot
        self.is_mock = settings.is_test
        self.raise_exception = raise_exception
        self.raised = False
        self.args = None

    def easy_call(self, *args, **kwargs):
        """Call the method by simplified params"""
        raise NotImplementedError

    def log(self, kwargs):
        raise NotImplementedError

    def call(self, **kwargs):
        """
        Call the method by the exact Telegram API params,
        by keyword arguments only, to easily validate them
        """
        self.args = self._validate(kwargs)
        success, response = self._call(self.args)
        if success:
            self.log(self.args)
        return success, response

    def __str__(self):
        if self.args:
            return f'{self.name}: {self.args}'
        else:
            return f'{self.name}: no args'

    def _get_parse_mode(self, html, markdown, markdown_v2):
        parse_mode = None
        if html:
            parse_mode = telegram.ParseMode.HTML
        elif markdown:
            parse_mode = telegram.ParseMode.MARKDOWN
        elif markdown_v2:
            parse_mode = telegram.ParseMode.MARKDOWN_V2
        return parse_mode

    def _get_method(self):
        if self.is_mock:

            def tgbot_method(**kwargs):
                if self.raise_exception is not None and not self.raised:
                    self.raised = True
                    raise self.raise_exception
                return ''

        else:
            tgbot_method = getattr(self.tgbot, self.name)

        return tgbot_method

    def _call(self, kwargs):
        """
        Retries, handling network and load issues
        """
        to_attempt = settings.api_attempts
        success, response = False, None
        tgbot_method = self._get_method()

        while to_attempt > 0:
            try:
                response = tgbot_method(**kwargs)
                success = True
                to_attempt = 0
            except telegram.error.NetworkError as exc:
                success, to_attempt = self._handle_network_error(exc, success, to_attempt)
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
                success, to_attempt = self._handle_unauthorized_or_bad(exc, success, to_attempt)
                response = exc.message

        logger.debug('Success' if success else 'Fail')
        return success, response

    def _handle_network_error(self, exc, success, to_attempt):
        success = False
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
                exc.message, settings.network_error_wait
            )
            to_attempt -= 1
            time.sleep(settings.network_error_wait)

        return success, to_attempt

    def _handle_unauthorized_or_bad(self, exc, success, to_attempt):
        success = False

        # telegram.error.Unauthorized
        if 'bot was kicked' in exc.message:
            logger.error(exc)
            to_attempt = 0

        else:
            logger.error('Error: "%s". Retrying', exc)
            to_attempt -= 2

        return success, to_attempt

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

    def call(self, **kwargs):
        """If bot was kicked from the chat, update Chat record in storage"""
        success, response = super().call(**kwargs)
        if not success and 'bot was kicked' in response:
            db.Chat.update_one({'id': kwargs['chat_id']}, {'_kicked_at': get_current_unixtime()})
        return success, response

    def easy_call(
            self, chat_id, text, reply_to=None, markup=None, preview=False, notify=True,
            force=True, html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, text=text, reply_to_message_id=reply_to, reply_markup=markup,
            parse_mode=parse_mode, disable_web_page_preview=not preview,
            disable_notification=not notify, allow_sending_without_reply=force, **kwargs,
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
    def easy_call(
            self, text, chat_id, message_id, preview=False,
            html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            text=text, chat_id=chat_id, message_id=message_id, parse_mode=parse_mode,
            disable_web_page_preview=not preview, **kwargs,
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
        success, response = self.call(chat_id=chat_id, message_id=message_id)
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

    def easy_call(
            self, chat_id, photo, reply_to=None, markup=None, notify=True, force=True,
            html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, photo=photo, reply_to_message_id=reply_to,
            reply_markup=markup, parse_mode=parse_mode, disable_notification=not notify,
            allow_sending_without_reply=force, **kwargs,
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
            self, chat_id, document, reply_to=None, markup=None, force=True,
            notify=True, html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, document=document, reply_to_message_id=reply_to, reply_markup=markup,
            parse_mode=parse_mode, disable_notification=not notify,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send document to chat %s', chat_id)


class SendAnimationMethod(ApiMethod):
    name = 'send_animation'
    parameters = (
        # required
        'chat_id', 'animation',
        # optional
        'duration', 'width', 'height', 'thumb', 'caption', 'parse_mode', 'caption_entities',
        'disable_notification', 'reply_to_message_id', 'allow_sending_without_reply',
        'reply_markup',
    )

    def easy_call(
            self, chat_id, animation, reply_to=None, markup=None, notify=True, force=True,
            html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, animation=animation, reply_to_message_id=reply_to,
            reply_markup=markup, disable_notification=not notify, parse_mode=parse_mode,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send animation to chat %s', chat_id)


class SendAudioMethod(ApiMethod):
    name = 'send_audio'
    parameters = (
        # required
        'chat_id', 'audio',
        # optional
        'caption', 'parse_mode', 'caption_entities', 'duration', 'performer', 'title', 'thumb',
        'disable_notification', 'reply_to_message_id', 'allow_sending_without_reply',
        'reply_markup',
    )

    def easy_call(
            self, chat_id, audio, reply_to=None, markup=None, notify=True, force=True,
            html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, audio=audio, reply_to_message_id=reply_to,
            reply_markup=markup, disable_notification=not notify, parse_mode=parse_mode,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send audio to chat %s', chat_id)


class SendVideoMethod(ApiMethod):
    name = 'send_video'
    parameters = (
        # required
        'chat_id', 'video',
        # optional
        'duration', 'width', 'height', 'thumb', 'caption', 'parse_mode', 'caption_entities',
        'supports_streaming', 'disable_notification', 'reply_to_message_id',
        'allow_sending_without_reply', 'reply_markup',
    )

    def easy_call(
            self, chat_id, video, reply_to=None, markup=None, notify=True, force=True,
            html=None, markdown=None, markdown_v2=None, **kwargs,
        ):
        parse_mode = self._get_parse_mode(html, markdown, markdown_v2)
        success, response = self.call(
            chat_id=chat_id, video=video, reply_to_message_id=reply_to,
            reply_markup=markup, disable_notification=not notify, parse_mode=parse_mode,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send video to chat %s', chat_id)


class SendStickerMethod(ApiMethod):
    name = 'send_sticker'
    parameters = (
        # required
        'chat_id', 'sticker',
        # optional
        'disable_notification', 'reply_to_message_id', 'allow_sending_without_reply',
        'reply_markup',
    )

    def easy_call(
            self, chat_id, sticker, reply_to=None, markup=None, notify=True, force=True, **kwargs,
        ):
        success, response = self.call(
            chat_id=chat_id, sticker=sticker, reply_to_message_id=reply_to,
            reply_markup=markup, disable_notification=not notify,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        logger.info('Send sticker to chat %s', chat_id)


class SendContactMethod(ApiMethod):
    name = 'send_contact'
    parameters = (
        # required
        'chat_id', 'phone_number', 'first_name',
        # optional
        'last_name', 'vcard', 'disable_notification', 'reply_to_message_id',
        'allow_sending_without_reply', 'reply_markup',
    )

    def easy_call(
            self, chat_id, phone_number, first_name, reply_to=None, markup=None, notify=True,
            force=True, **kwargs,
        ):
        success, response = self.call(
            chat_id=chat_id, phone_number=phone_number, first_name=first_name,
            reply_to_message_id=reply_to, reply_markup=markup, disable_notification=not notify,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        phone_number = kwargs.get('phone_number')
        logger.info('Send contact %s to chat %s', phone_number, chat_id)


class SendLocationMethod(ApiMethod):
    name = 'send_location'
    parameters = (
        # required
        'chat_id', 'latitude', 'longitude',
        # optional
        'horizontal_accuracy', 'live_period', 'heading', 'proximity_alert_radius',
        'disable_notification', 'reply_to_message_id', 'allow_sending_without_reply',
        'reply_markup',
    )

    def easy_call(
            self, chat_id, lat, lon, reply_to=None, markup=None, notify=True, force=True, **kwargs,
        ):
        success, response = self.call(
            chat_id=chat_id, latitude=lat, longitude=lon, reply_to_message_id=reply_to,
            reply_markup=markup, disable_notification=not notify,
            allow_sending_without_reply=force, **kwargs,
        )
        return success, response

    def log(self, kwargs):
        chat_id = kwargs.get('chat_id')
        lat = kwargs.get('latitude')
        lon = kwargs.get('longitude')
        logger.info('Send location (%s, %s) to chat %s', lat, lon, chat_id)


api_methods = {
    'send_message': SendMessageMethod,
    'send_photo': SendPhotoMethod,
    'send_document': SendDocumentMethod,
    'send_animation': SendAnimationMethod,
    'edit_message_text': EditMessageTextMethod,
    'delete_message': DeleteMessageMethod,
    'forward_message': ForwardMessageMethod,
    'send_sticker': SendStickerMethod,
    'send_audio': SendAudioMethod,
    'send_video': SendVideoMethod,
    'send_contact': SendContactMethod,
    'send_location': SendLocationMethod,
}
