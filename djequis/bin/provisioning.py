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

from djequis.sql.provisioning import CURRENT_EMPLOYEES, CURRENT_STUDENTS

from djzbar.utils.informix import do_sql
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from openpyxl import Workbook
from openpyxl import load_workbook

import csv
import time
import argparse


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
    '--test',
    action='store_true',
    help="Dry run?",
    dest='test'
)

TIMESTAMP = time.strftime("%Y%m%d%H%M%S")


def _gen_files(results, group):

    status = False
    if results is not None:

        root = '{}/{}_{}'.format(
            settings.PROVISIONING_DATA_DIRECTORY, group, TIMESTAMP
        )
        phile = ('{}.csv'.format(root))

        # create .csv file
        csvfile = open(phile,"w")
        output = csv.writer(csvfile)

        # load our XLSX template
        wb = load_workbook(
            '{}/static/xml/{}.xlsx'.format(settings.ROOT_DIR, group)
        )
        # obtain the active worksheet
        ws = wb.active

        for result in results:
            output.writerow(result)
            row = []
            for r in result:
                row.append(r)
            ws.append(row)

        # Save the file
        wb.save('{}.xlsx'.format(root))
        # close the csv file
        csvfile.close()
        status = True

    return status


def main():
    """
    main function
    """

    key = None

    if database == 'train':
        EARL = INFORMIX_EARL_TEST
    elif database == 'cars':
        EARL = INFORMIX_EARL_PROD
    else:
        print("database must be: 'cars' or 'train'\n")
        parser.print_help()
        exit(-1)

    # Current Students
    if test:
        print('current students sql')
        print("sql = {}".format(CURRENT_STUDENTS))
    else:
        students  = do_sql(CURRENT_STUDENTS, key=key, earl=EARL)
        response = _gen_files(students, 'current_students')

    # Current Employees

    if test:
        print('current employees sql')
        print("sql = {}".format(CURRENT_EMPLOYEES))
    else:
        employees = do_sql(CURRENT_EMPLOYEES, key=key, earl=EARL)
        response = _gen_files(employees, 'current_employees')


######################
# shell command line
######################

if __name__ == '__main__':
    args = parser.parse_args()
    test = args.test
    database = args.database.lower()

    sys.exit(main())
