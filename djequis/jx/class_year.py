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

from djzbar.utils.informix import get_session


import csv

# set up command-line options
desc = """
    updates the class_year table,
    setting it to 0 where it equals 9999
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "-a", "--action",
    help="select or update.",
    dest="action"
)
parser.add_argument(
    "-d", "--database",
    help="database name.",
    dest="database"
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

    if database == 'jxtest':
        EARL = settings.JX_EARL_TEST
    elif database == 'jxlive':
        EARL = settings.JX_EARL_PROD
    else:
        EARL = None

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
    database = args.database
    test = args.test

    if not action or not database:
        print "mandatory options are missing: database and action\n"
        parser.print_help()
        exit(-1)
    else:
        action = action.lower()
        database = database.lower()

    if database != 'jxlive' and database != 'jxtest':
        print "database must be: 'jxlive' or 'jxtest'\n"
        parser.print_help()
        exit(-1)

    if action != 'select' and action != 'update':
        print "action must be: 'select' or 'update'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())

