from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from djequis.core.admissions.sms.forms import SendForm

from djtools.utils.logging import seperator


class CoreFormsTestCase(TestCase):

    def setUp(self):
        pass

    def test_student_detail_valid_data(self):
        form = StudentDetailForm({
            'student_number': settings.TEST_STUDENT_ID,
        })
        self.assertTrue(form.is_valid())

    def test_student_detail_invalid_data(self):
        form = StudentDetailForm({
            'student_number': '867-5309',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'student_number': ['Enter a whole number.'],
        })

    def test_student_detail_blank_data(self):
        form = StudentDetailForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'student_number': ['This field is required.'],
        })

