from django.conf import settings
from django.test import TestCase

from djtools.utils.logging import seperator

from twilio.rest import Client


class CoreViewsTestCase(TestCase):

    def setUp(self):

        self.client = Client(
            settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
        )
        self.to = settings.TWILIO_TEST_TO
        self.frum = settings.TWILIO_FROM_PHONE

    def test_send(self):
        print "\n"
        print "send an sms message"
        seperator()

        self.client.messages.create(
            to = self.to,
            from_ = self.frum,
            # use parentheses to prevent extra whitespace
            body = (
                "Test text message via Django Unit Test\n"
                "Who does your accounting?"
            )
        )
