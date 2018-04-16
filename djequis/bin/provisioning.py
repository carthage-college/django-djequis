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

import django
django.setup()

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

from djequis.sql.provisioning import INSERT_EMAIL_RECORD
from djequis.sql.provisioning import INSERT_CVID_RECORD
from djequis.sql.provisioning import SELECT_NEW_PEOPLE

from djzbar.utils.informix import do_sql
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from openpyxl import Workbook
from openpyxl import load_workbook

import csv
import time
import argparse
import logging


"""
provising framework for new students and employees
"""

# set up command-line options
desc = """
Accepts as input a database name
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    '-d', '--database',
    required=True,
    help="Database name (cars or train).",
    dest='database'
)
parser.add_argument(
    '-f', '--filetype',
    required=True,
    help="File type (csv or xlsx).",
    dest='filetype'
)
parser.add_argument(
    '--test',
    action='store_true',
    help="Dry run?",
    dest='test'
)

TIMESTAMP = time.strftime("%Y%m%d%H%M%S")

# create logger for collecting failed inserts
logger = logging.getLogger(__name__)
# create handler and set level to info
handler = logging.FileHandler('{}provisioning.log'.format(
    settings.LOG_FILEPATH)
)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def _gen_files(results, filetype, group):
    """
        Active Directory required fields in order:

        loginID, lastName, firstName, nameID,
        [facultyStatus, staffStatus, studentStatus, retireStatus,]
        dob, zip, acct-types, proxID, phoneExt, depts

        at least one of the Status fields must be populated
    """

    status = False
    if results:

        root = '{}{}_{}'.format(
            settings.PROVISIONING_DATA_DIRECTORY, group, TIMESTAMP
        )

        if filetype == 'csv':
            # create .csv file
            phile = ('{}.csv'.format(root))
            csvfile = open(phile,"w")
            output = csv.writer(csvfile)

            for result in results:
                print result
                output.writerow(result)

            # close the csv file
            csvfile.close()
            status = True

        elif filetype == 'xlsx':
            # load our XLSX template
            wb = load_workbook(
                '{}/static/xml/{}.xlsx'.format(settings.ROOT_DIR, group)
            )
            # obtain the active worksheet
            ws = wb.active

            for result in results:
                row = []
                for r in result:
                    row.append(r)
                ws.append(row)

            # Save the xml file
            wb.save('{}.xlsx'.format(root))
            status = True

        else:
            print("filetype must be: 'csv' or 'xlsx'\n")
            parser.print_help()
            exit(-1)


    return status


def main():
    """
    main function
    """

    key = 'debug'

    if filetype not in ['csv','xlsx']:
        print("filetype must be: 'csv' or 'xlsx'\n")
        parser.print_help()
        exit(-1)

    if database == 'train':
        EARL = INFORMIX_EARL_TEST
    elif database == 'cars':
        EARL = INFORMIX_EARL_PROD
    else:
        print("database must be: 'cars' or 'train'\n")
        parser.print_help()
        exit(-1)

    sql = SELECT_NEW_PEOPLE
    if test:
        print("new people sql")
        print("sql = {}".format(sql))
    else:
        people = []
        objects = do_sql(sql, key=key, earl=EARL)
        for o in objects:
            people.append(o)
        response = _gen_files(people, filetype, 'new_people')

        print("response = {}".format(response))
        if not response:
            print("no response")
        else:
            for p in people:
                print p
                '''
                try:
                    sql = INSERT_EMAIL_RECORD.format(cid=p.id, ldap=p.loginID)
                    do_sql(sql, key=key, earl=EARL)
                except:
                    logger.info("failed insert = {}".format(sql))
                try:
                    sql = INSERT_CVID_RECORD.format(cid=p.id, ldap=p.loginID)
                    do_sql(sql, key=key, earl=EARL)
                except:
                    logger.info("failed insert = {}".format(sql))
                '''


######################
# shell command line
######################

if __name__ == '__main__':
    args = parser.parse_args()
    test = args.test
    database = args.database.lower()
    filetype = args.filetype.lower()

    sys.exit(main())
