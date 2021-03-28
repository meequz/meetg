import telegram

import settings
from meetg.tests.base import AnyHandlerBotCase
from meetg.testing import get_sample


class AnswerTest(AnyHandlerBotCase):

    def test_answer_text(self):
        self.bot.send_message(1, 'bot sends this')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_method.args['chat_id'] == 1
        assert self.bot.last_method.args['text'] == 'bot sends this'

    def test_answer_image(self):
        self.bot.send_photo(1, photo=get_sample('png_2px.png'))
        assert self.bot.last_method.name == 'send_photo'
        assert isinstance(self.bot.last_method.args['photo'], bytes)

    def test_answer_gif(self):
        self.bot.send_document(1, document=get_sample('gif_animation.gif'))
        assert self.bot.last_method.name == 'send_document'
        assert isinstance(self.bot.last_method.args['document'], bytes)

    def test_answer_mp4_animation(self):
        self.bot.send_animation(1, animation=get_sample('no_sound.mp4'))
        assert self.bot.last_method.name == 'send_animation'
        assert isinstance(self.bot.last_method.args['animation'], bytes)

    def test_answer_audio(self):
        self.bot.send_audio(1, audio=get_sample('audio.mp3'))
        assert self.bot.last_method.name == 'send_audio'
        assert isinstance(self.bot.last_method.args['audio'], bytes)

    def test_answer_video(self):
        self.bot.send_video(1, video=get_sample('video.mp4'))
        assert self.bot.last_method.name == 'send_video'
        assert isinstance(self.bot.last_method.args['video'], bytes)

    def test_answer_animated_sticker(self):
        self.bot.send_sticker(1, sticker=get_sample('animated_sticker.tgs'))
        assert self.bot.last_method.name == 'send_sticker'
        assert isinstance(self.bot.last_method.args['sticker'], bytes)

    def test_answer_not_animated_sticker(self):
        self.bot.send_sticker(1, sticker=get_sample('sticker.webp'))
        assert self.bot.last_method.name == 'send_sticker'
        assert isinstance(self.bot.last_method.args['sticker'], bytes)

    def test_answer_contact(self):
        self.bot.send_contact(1, phone_number='+3751234567', first_name='Cihan')
        assert self.bot.last_method.name == 'send_contact'
        assert self.bot.last_method.args['phone_number'] == '+3751234567'
        assert self.bot.last_method.args['first_name'] == 'Cihan'

    def test_answer_location(self):
        self.bot.send_location(1, lat=52.0, lon=-12.1)
        assert self.bot.last_method.name == 'send_location'
        assert self.bot.last_method.args['latitude'] == 52.0
        assert self.bot.last_method.args['longitude'] == -12.1


class ReceiveTest(AnyHandlerBotCase):

    def test_receive_text(self):
        self.bot.receive_message('Spam')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.text == 'Spam'

    def test_receive_image(self):
        self.bot.receive_message(photo__file_id='BfaqFvb')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.photo[0].file_id == 'BfaqFvb'

    def test_receive_gif(self):
        self.bot.receive_message(document__mime_type='image/gif')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.document.mime_type == 'image/gif'

    def test_receive_mp4_animation(self):
        self.bot.receive_message(animation__mime_type='video/mp4')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.animation.mime_type == 'video/mp4'

    def test_receive_animated_sticker(self):
        self.bot.receive_message(sticker__is_animated=True)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.sticker.is_animated == True

    def test_receive_not_animated_sticker(self):
        self.bot.receive_message(sticker__is_animated=False)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.sticker.is_animated == False

    def test_receive_audio(self):
        self.bot.receive_message(audio__duration=15)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.audio.duration == 15

    def test_receive_video(self):
        self.bot.receive_message(video__duration=21)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.video.duration == 21

    def test_receive_contact(self):
        self.bot.receive_message(contact__phone_number='+123456789')
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.contact.phone_number == '+123456789'

    def test_receive_location(self):
        self.bot.receive_message(location__longitude=-36, location__latitude=45)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_update.effective_message.location.longitude == -36
        assert self.bot.last_update.effective_message.location.latitude == 45


class ErrorTest(AnyHandlerBotCase):

    def test_chat_migrated(self):
        exception = telegram.error.ChatMigrated(new_chat_id=2)
        self.bot.send_message(1, 'Spam', raise_exception=exception)
        assert self.bot.last_method.name == 'send_message'
        assert self.bot.last_method.args['chat_id'] == 2


class ReportTest(AnyHandlerBotCase):

    def setUp(self):
        super().setUp()
        settings.report_to = (1, )

    def test_report_msg_broadcasted(self):
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        assert self.bot.last_method.args['text'].startswith('#report\n@mock_username for the')

    def test_number_of_api_objects_in_report(self):
        self.bot.receive_message('Spam')
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        broadcasted = self.bot.last_method.args['text']
        assert 'stored 1 new chats' in broadcasted
        assert 'stored 1 new messages' in broadcasted
        assert 'stored 1 new updates' in broadcasted
        assert 'stored 1 new users' in broadcasted

    def test_job_time_in_report(self):
        self.bot.receive_message('Spam')
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        stats_job()
        broadcasted = self.bot.last_method.args['text']
        assert '_job_report_stats took' in broadcasted

    def test_no_action_if_empty_report_to(self):
        settings.report_to = ()
        stats_job = self.bot._job_queue_wrapper._wrapped_callbacks[0]
        stats_job()
        assert not self.bot.last_method
