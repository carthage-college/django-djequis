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
    Test the API for obtaining users. See for endpoint description:
    http://developers.schoology.com/api-documentation/rest-api-v1/user
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

        print ("""
            uid: {}
            id: {}
            school_id: {}
            synced: {}
            school_uid: {}
            additional_buildings
            name_title: {}
            name_title_show
            name_first: {}
            name_first_preferred: {}
            name_middle: {}
            name_middle_show: {}
            name_last: {}
            name_display: {}
            username: {}
            primary_email: {}
            picture_url: {}
            gender: {}
            position: {}
            grad_year: {}
            password: {}
            role_id: {}
            tz_offset: {}
            tz_name: {}
            child_uids: {}
        """.format(
            user.uid, user.id, user.school_id, user.synced, user.school_uid,
            user.additional_buildings, user.name_title, user.name_title_show,
            user.name_first, user.name_first_preferred, user.name_middle,
            user.name_middle_show, user.name_last, user.name_display,
            user.username, user.primary_email, user.picture_url, user.gender,
            user.position, user.grad_year, user.password, user.role_id,
            user.tz_offset, user.tz_name, user.child_uids
        ))


if __name__ == '__main__':
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
