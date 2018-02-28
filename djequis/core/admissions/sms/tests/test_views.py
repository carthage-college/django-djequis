from django.conf import settings
from django.test import TestCase

from djtools.utils.logging import seperator

from djequis.core.admissions.sms.client import twilio_client as client
from djequis.core.admissions.sms.manager import Message
from djequis.core.admissions.sms.errors import MESSAGE_DELIVERY_CODES

from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException


class CoreViewsTestCase(TestCase):

    def setUp(self):

        self.client = client
        self.to = settings.TWILIO_TEST_PHONE_TO
        self.from_valid = settings.TWILIO_TEST_PHONE_FROM
        self.from_invalid = settings.TWILIO_TEST_PHONE_FROM_INVALID
        self.mssid = settings.TWILIO_TEST_MESSAGING_SERVICE_SID
        self.message = Message()

    def test_send_valid(self):
        print "\n"
        print "send an sms message"
        seperator()
        die = False
        if settings.DEBUG:
            try:
                response = self.client.messages.create(
                    to = self.to,
                    #from_ = self.from_valid,
                    messaging_service_sid = self.mssid,
                    # use parentheses to prevent extra whitespace
                    body = (
                        "Test sms message via Python Unit Test\n"
                        "Who does your taxes?"
                    ),
                    status_callback = 'https://requestb.in/19mnap81'
                )
            except TwilioRestException as e:
                die = True
                print "REST Error message:"
                seperator()
                print e

            if not die:
                print response.__dict__
                print "response sid:"
                sid = response.sid

                '''
                r = MessagingResponse()
                r.message(message, to=to, sender=sender, method='POST',
                action=action,
                media=media)
                '''
                message = self.message.status(sid, 'delivered')
                if message.status == 'delivered':
                    print "Success: message sent"
                    print message.__dict__
                else:
                    print "Fail: message was not sent:"
                    print message.error_message
                    print MESSAGE_DELIVERY_CODES[message.error_code].description
        else:
            print "use the --debug-mode flag to test message delivery"

    def test_send_invalid_from(self):
        print "\n"
        print "send an sms message from invalid from number"
        seperator()
        if settings.DEBUG:
            try:
                response = self.client.messages.create(
                    to = self.to,
                    from_ = self.from_invalid,
                    # use parentheses to prevent extra whitespace
                    body = (
                        "Test sms message via Python Unit Test\n"
                        "Who does your taxes?"
                    )
                )
            except TwilioRestException as e:
                print "REST Error message:"
                seperator()
                print e

        else:
            print "use the --debug-mode flag to test message delivery"
