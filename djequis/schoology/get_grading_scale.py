#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
import argparse

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

desc = """
    Test the API for obtaining grading scales. See for endpoint description:
    https://developers.schoology.com/api-documentation/rest-api-v1/grading-scales
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-s', '--section-id',
    required=True,
    help="course section ID",
    dest='section_id'
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

    grading_scale = sc.get_grading_scale(section_id)

    # empty json() method = '{}'
    if len(grading_scale.json()) > 2:

        for gs in grading_scale['grading_scale'][0]['scale']['level']:
            print(gs)


if __name__ == '__main__':
    args = parser.parse_args()
    section_id = args.section_id
    test = args.test

    sys.exit(main())
