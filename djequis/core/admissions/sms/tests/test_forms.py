from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from djequis.core.admissions.sms.forms import SendForm

from djtools.utils.logging import seperator


class SendFormTestCase(TestCase):

    def setUp(self):
        pass

    def test_send_form_valid_data(self):
        form = SendForm({
            'phone_to': settings.TWILIO_TEST_PHONE_TO,
            'message': settings.TWILIO_TEST_MESSAGE
        })
        self.assertTrue(form.is_valid())

    def test_send_form_invalid_data(self):
        form = SendForm({
            'phone_to': '8675309',
            'message': '',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'phone_to': ['Phone numbers must be in XXX-XXX-XXXX format.'],
            'message': ['This field is required.'],
        })

    def test_send_form_blank_data(self):
        form = SendForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'phone_to': ['This field is required.'],
            'message': ['This field is required.'],
        })
