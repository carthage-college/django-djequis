#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django
import argparse
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
    '-i', '--section-id',
    required=True,
    help="course section ID",
    dest='section_id'
)
parser.add_argument(
    '-s', '--score',
    required=True,
    help="course score",
    dest='score'
)
parser.add_argument(
    '-e', '--scale',
    required=True,
    help="scale ID",
    dest='scale'
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

    # empty json() method = '{}' so we fetch json file that contains
    # the default grading scales
    if len(grading_scale.json()) == 2:

        # convert json data from file to python dictionary
        grading_scale = json.load(
            open(settings.SCHOOLOGY_TEST_GRADING_SCALE_FILE)
        )

    if test:
        print(grading_scale)

    final = 0
    for g in grading_scale['grading_scale']:
        if g['id'] == scale:
            for level in g['scale']['level']:
                if score >= level['cutoff']:
                    final = level['grade']

    print(final)


if __name__ == '__main__':
    args = parser.parse_args()
    section_id = args.section_id
    # make sure grade is an integer
    score = int(args.score)
    scale= int(args.scale)
    test = args.test

    sys.exit(main())
