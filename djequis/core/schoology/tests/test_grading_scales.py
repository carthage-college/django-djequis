from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from djtools.utils.logging import seperator

from schoolopy import Schoology, Auth

import json

import logging
logger = logging.getLogger('djequis')


class CoreSchoologyViewsTestCase(TestCase):

    def setUp(self):
        self.sc = Schoology(
            Auth(settings.SCHOOLOGY_API_KEY, settings.SCHOOLOGY_API_SECRET)
        )

    def test_grading_scales(self):

        print("\n")
        print("grading scales")
        print(seperator())

        grading_scale = sc.get_grading_scale(section_id)
