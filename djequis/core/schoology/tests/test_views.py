from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from djequis.core.schoology.sql import SELECT_GRADE, UPDATE_GRADE

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
        self.json_data_bad = json.load(
            open(settings.SCHOOLOGY_TEST_GRADES_TRIGGER_JSON_FILE_BAD)
        )

    def test_trigger_grades_json(self):

        print("\n")
        print("trigger grades JSON")
        print(seperator())

        data = self.json_data
        # simple check for one json parameter
        self.assertIn(data['type'], 'grades.update')

    def test_trigger_grades_view(self):

        print("\n")
        print("trigger grades view")
        print(seperator())

        response = self.client.post(
            reverse('trigger_grades'), json.dumps(self.json_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Success')

    def test_trigger_grades_update(self):

        print("\n")
        print("trigger grades update informix")
        print(seperator())

        data = self.json_data

        session = get_session(self.earl)

        for grade in data['data']:
            # 01234567890123456789012345678
            # 2018;RC;FRN 2010;01;UG17;UNDG
            # yr  sess crs_no  sec cat prog
            school_code = grade['section_school_code']

            # use the --debug-mode flag to test with SELECT
            if settings.DEBUG:
                sql = SELECT_GRADE(
                    coursekey = school_code,
                    student_number = grade['school_uid']
                )
            else:
                sql = UPDATE_GRADE(
                    grade = grade['updated_overall_grade'],
                    coursekey = school_code,
                    student_number = grade['school_uid']
                )

            print("sql = {}".format(sql))

            print("2018;RC;FRN 2010;01;UG17;UNDG")
            print("yr  sess crs_no  sec cat prog")
            print("cw_rec.yr = {}".format(school_code[0:4]))
            print("cw_rec.cat = {}".format(school_code[20:25]))
            print("cw_rec.sess = {}".format(school_code[5:7]))
            print("cw_rec.prog = {}".format(school_code[25:]))
            print("cw_rec.crs_no = {}".format(school_code[8:16]))
            print("cw_rec.sec = {}".format(school_code[17:19]))

            try:
                response = session.execute(sql)
                if settings.DEBUG:
                    for r in response:
                        print(r)
            except:
                logger.debug('test_trigger_grades_update_bad_data = {}'.format(
                    grade
                ))

        session.close()

    def test_trigger_grades_update_bad_data(self):

        print("\n")
        print("trigger grades update informix with bad data")
        print(seperator())

        data = self.json_data_bad
 
        session = get_session(self.earl)

        for grade in data['data']:

            try:
                school_code = grade['section_school_code']
                sql = UPDATE_GRADE(
                    grade = grade['updated_overall_grade'],
                    coursekey = school_code,
                    student_number = grade['school_uid']
                )

                print("update grade sql = {}".format(sql))

                response = session.execute(sql)
            except:
                logger.debug('test_trigger_grades_update_bad_data = {}'.format(
                    grade
                ))

