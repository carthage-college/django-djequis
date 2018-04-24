from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from djtools.utils.logging import seperator
from djzbar.utils.informix import get_session

import json

import logging
logger = logging.getLogger('djequis')


class CoreSchoologyViewsTestCase(TestCase):

    fixtures = []

    def setUp(self):
        pass
        self.earl = settings.INFORMIX_EARL
        self.json_data = json.load(
            open(settings.SCHOOLOGY_TEST_GRADES_TRIGGER_JSON_FILE)
        )

    def test_trigger_grades_json(self):

        print("\n")
        print("trigger grades JSON")
        print(seperator())

        data = self.json_data
        print(data)

        print(data['uid'])

    def test_trigger_grades_view(self):

        print("\n")
        print("trigger grades view")
        print(seperator())

        data = self.json_data


        response = self.client.post(
            reverse('trigger_grades'), data
        )

        print(response)

        print("update informix")

        # create the ctc_blob object with the value of the message body for txt
        session = get_session(self.earl)

        sql = 'select * from jenzcrs_rec limit 100'

        print("insert sql statement:\n{}".format(sql))
        logger.debug('sql = {}'.format(sql))


        objects = session.execute(sql)
        for o in objects:
            print o

        #session.commit()
