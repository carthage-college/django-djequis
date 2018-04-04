# -*- coding: utf-8 -*-
import os
import sys
import argparse
import urllib2
import json

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
import django
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
    Test the API for obtaining users. See for endpoint description:
    http://developers.schoology.com/api-documentation/rest-api-v1/user
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-', '--section-id',
    required=True,
    help="course section ID",
    dest='sid'
)
parser.add_argument(
    '-a', '--assignment-id',
    required=False,
    help="filter grades for a given assignment",
    dest='aid'
)
parser.add_argument(
    '-e', '--enrollment-id',
    required=False,
    help="filter grades for a given enrollment",
    dest='eid'
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

    # Only retrieve 10 objects max
    sc.limit = 10

    print("Your name is {}".format(sc.get_me().name_display))

    if aid:
        gid = aid
        filter_type = 'assignment_id'
    elif eid:
        gid = eid
        filter_type = 'enrollment_id'

    grades = sc.get_section_grades(sid, gid, filter_type)


if __name__ == "__main__":
    args = parser.parse_args()
    aid = args.aid
    eid = args.eid
    sid = args.sid
    test = args.test

    if not aid and not eid:
        print("you must provide an assignment ID or enrollment ID\n")
        parser.print_help()
        exit(-1)

    sys.exit(main())
