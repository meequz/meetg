from telegram.ext import Filters, MessageHandler

from meetg.botting import BaseBot
from meetg.testing import BaseStorageTestCase
from meetg.utils import get_update_type


class MeetgBaseTestCase(BaseStorageTestCase):
    pass


class AnyHandlerBot(BaseBot):
    """
    The simplest bot with just one very wide handler
    """
    def init_handlers(self):
        handlers = (MessageHandler(Filters.all, self.reply_any), )
        return handlers

    def reply_any(self, update, context):
        chat_id = update.effective_chat.id
        self.send_message(chat_id, update.to_json())


class AnyHandlerBotCase(MeetgBaseTestCase):

    def setUp(self):
        super().setUp()
        self.bot = AnyHandlerBot(mock=True)
