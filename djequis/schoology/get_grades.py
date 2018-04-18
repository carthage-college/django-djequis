#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
import argparse
import datetime
import urllib2
import json
import time

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
django.setup()

from schoolopy import Schoology, Auth

# django settings for script
from django.conf import settings

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

desc = """
    Test the API for obtaining grades. See for endpoint description:
    http://developers.schoology.com/api-documentation/rest-api-v1/grade
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-s', '--section-id',
    required=True,
    help="course section ID",
    dest='section_id'
)
parser.add_argument(
    '-a', '--assignment-id',
    required=False,
    help="filter grades for a given assignment",
    dest='assignment_id'
)
parser.add_argument(
    '-e', '--enrollment-id',
    required=False,
    help="filter grades for a given enrollment",
    dest='enrollment_id'
)
parser.add_argument(
    '-t', '--timestamp',
    required=False,
    help="filter grades by a date and time. format: %Y-%m-%d",
    dest='timestamp'
)
parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)


def main():

    sc = Schoology(
        Auth(settings.SCHOOLOGY_API_KEY, settings.SCHOOLOGY_API_SECRET)
    )

    if assignment_id:
        query_name = 'assignment_id'
        query_value = assignment_id
    elif enrollment_id:
        query_name = 'enrollment_id'
        query_value = enrollment_id
    elif timestamp:
        query_name = 'timestamp'
        query_value = str(time.mktime(
            datetime.datetime.strptime(timestamp, "%Y-%m-%d").timetuple()
        ))[:-2] # remove milliseconds
    else:
        query_name = None
        query_value = None

    grades = sc.get_section_grades(section_id, query_name, query_value)

    for g in grades:
        line = (
            "asignment id = {}, enrollment_id = {}, timestamp = {}, "
            "comment = {}, grade = {}, web_url = {}, comment_status = {}, "
            "scale_type = {}, exception = {}, g.calculated_grade = {}, "
            "scale_id = {}, school_uid = {}, max_points = {}, "
            "location = {}, assignment_type = {}, override = {}, "
            "category_id = {}, type = {}, pending = {}, is_final = {}"
        ).format(
            g.assignment_id, g.enrollment_id, g.timestamp, g.comment, g.grade,
            g.web_url, g.comment_status, g.scale_type, g.exception,
            g.calculated_grade, g.scale_id, g.school_uid, g.max_points,
            g.location, g.assignment_type, g.override, g.category_id, g.type,
            g.pending, g.is_final
        )

        print(line)


if __name__ == '__main__':
    args = parser.parse_args()
    assignment_id = args.assignment_id
    enrollment_id = args.enrollment_id
    section_id = args.section_id
    timestamp = args.timestamp
    test = args.test

    sys.exit(main())
