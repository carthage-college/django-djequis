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
    Test the API for obtaining all sections.
    Currently returns 403 Forbidden
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

    sections = sc.get_sections()

    print(sections)


if __name__ == '__main__':
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
