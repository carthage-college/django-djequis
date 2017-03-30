# -*- coding: utf-8 -*-
import os
import sys
import argparse

# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

from django.conf import settings

from djczech.reconciliation.data.models import Cheque
from djzbar.utils.informix import get_session
from djtools.fields import TODAY

from datetime import date, datetime
from itertools import islice

from sqlalchemy import exc


"""
"""

import csv

EARL = settings.JX_EARL_PROD
#EARL = settings.JX_EARL_TEST

# set up command-line options
desc = """
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "-a", "--action",
    help="select or update.",
    dest="action"
)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    """
    main function
    """

    session = get_session(EARL)
    if action == 'update':
        sql = '''
            UPDATE
                class_year
            SET
                class_year=0
            WHERE
                class_year=9999
        '''
        objs = session.execute(sql)
        if test:
            print "row count = {}".format(objs.rowcount)
            print objs.context.statement
            print objs.context.engine
        else:
            session.commit()
    elif action == 'select':
        sql = '''
            SELECT
                *
            FROM
                class_year
            WHERE
                class_year=9999
        '''
        objs = session.execute(sql)
        years = objs.fetchall()
        for y in years:
            print y
    else:
        print 'how did that happen?'
        sys.exit()

    # fin
    session.close()


######################
# shell command line
######################

if __name__ == "__main__":
    args = parser.parse_args()
    action = args.action
    test = args.test

    if action:
        action = action.lower()
    else:
        print "mandatory option is missing: action\n"
        parser.print_help()
        exit(-1)

    if action != 'select' and action != 'update':
        print "action must be: 'select' or 'update'\n"
        parser.print_help()
        exit(-1)
    sys.exit(main())

