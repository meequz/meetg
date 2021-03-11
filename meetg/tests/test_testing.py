"""Tests for various things related to testing"""
from telegram.messageentity import MessageEntity

from meetg.entities import parse_entities
from meetg.factories import MessageFactory
from meetg.testing import BaseTestCase


class ParseEntitiesTest(BaseTestCase):
    STRING = '/de e@ma.il #hashtag /ita4li_1- meeq@uz'

    def _filter_by_type(self, entities, type):
        return [ent for ent in entities if ent.type == type]

    def test_email(self):
        entities = parse_entities('de e@ma.il a4li_1- meeq@uz')
        assert len(entities) == 1
        assert entities[0].type == MessageEntity.EMAIL
        assert entities[0].offset == 3
        assert entities[0].length == 7

    def test_command(self):
        entities = parse_entities('/de e@ma.il /a4li_1- meeq@uz')
        assert len(entities) == 3
        command_entities = self._filter_by_type(entities, MessageEntity.BOT_COMMAND)
        assert len(command_entities) == 2

        for command_entity in command_entities:
            assert command_entity.offset in (0, 12)
            assert command_entity.length in (3, 7)

    def test_hashtag(self):
        entities = parse_entities('#789 #789a')
        assert len(entities) == 1
        assert entities[0].type == MessageEntity.HASHTAG
        assert entities[0].offset == 5
        assert entities[0].length == 5

    def test_mention(self):
        entities = parse_entities('e@ma.il @kakby1')
        mention_entities = self._filter_by_type(entities, MessageEntity.MENTION)
        assert len(mention_entities) == 1
        assert mention_entities[0].type == MessageEntity.MENTION
        assert mention_entities[0].offset == 8
        assert mention_entities[0].length == 7

    def test_phone_number(self):
        entities = parse_entities('asd +12345678901 +1234567890')
        assert len(entities) == 1
        assert entities[0].type == MessageEntity.PHONE_NUMBER
        assert entities[0].offset == 4
        assert entities[0].length == 12

    def test_url(self):
        entities = parse_entities('monty https://www.debuggex.com/')
        assert len(entities) == 1
        assert entities[0].type == MessageEntity.URL
        assert entities[0].offset == 6
        assert entities[0].length == 25


class MessageFactoryTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.factory = MessageFactory(None, 'message')

    def test_type_is_group_if_new_chat_members(self):
        new_chat_members = [{'is_bot': True, 'username': 'mock_username'}]
        message = self.factory.create(new_chat_members=new_chat_members)
        assert message.chat.id < 0
        assert message.chat.type == 'group'
