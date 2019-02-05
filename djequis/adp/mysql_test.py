#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djequis.settings')

# required if using django models
import django
django.setup()

from django.db import connections

import argparse
import logging

logger = logging.getLogger('djequis')

'''
Shell script...
'''

# set up command-line options
desc = """
Accepts as input...
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-d', '--database',
    required=True,
    help="Database connection name from settings e.g. default",
    dest='database'
)
parser.add_argument(
    '-s', '--sql',
    required=True,
    help="A simple SQL incantation for testing e.g. 'SELECT * FROM auth_user'",
    dest='sql'
)
parser.add_argument(
    '--test',
    action='store_true',
    help="Dry run?",
    dest='test'
)

def main():
    '''
    main function
    '''

    print("hello")

    cursor = connections[database].cursor()

    if test:
        print(sql)
    else:
        cursor.execute(sql)
        objects = cursor.fetchall()

        for o in objects:
            print(o)


######################
# shell command line
######################

if __name__ == '__main__':
    args = parser.parse_args()
    database = args.database
    sql = args.sql
    test = args.test

    if test:
        print(args)

    sys.exit(main())


