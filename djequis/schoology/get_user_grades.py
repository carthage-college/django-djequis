#!/usr/bin/env python
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
    Test the API for obtaining user grades. See for endpoint description:
    http://developers.schoology.com/api-documentation/rest-api-v1/user-grades
"""

parser = argparse.ArgumentParser(description=desc)

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

    users =  sc.get_users()

    for user in users:
        print user.uid, user.id, user.username, user.school_uid
        grades = sc.get_user_grades(user.id)
        if grades:
            print grades[0].section_id
            #for a in grades[0].period[0]['assignment']:
                #print a


if __name__ == '__main__':
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
