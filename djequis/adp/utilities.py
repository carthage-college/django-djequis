import string
import datetime
import os
import io
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import datetime, timedelta
import time
from time import strftime
import argparse
import uuid
from sqlalchemy import text
import shutil
import re
import logging
from logging.handlers import SMTPHandler
import codecs
import unicodedata


# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
sys.path.append('/djequis/adp')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# # django settings for script
from django.conf import settings
from django.db import connections

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djtools.fields import TODAY

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
parser.add_argument(
    "-d", "--database",
    help="database name.",
    dest="database"
)

# set global variable
global EARL
# determines which database is being called from the command line
# if database == 'cars':
#    EARL = INFORMIX_EARL_PROD
# elif database == 'train':
# EARL = INFORMIX_EARL_TEST
EARL = INFORMIX_EARL_SANDBOX
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
engine = get_engine(EARL)

#########################################################
# Common function to validate that a record exists
#########################################################


def fn_validate_field(searchval, keyfield, retfield, table, keytype):
    if keytype == "char":
        qval_sql = "SELECT DISTINCT " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = '" + str(searchval) + "'"
    elif keytype == "integer":
        qval_sql = "SELECT DISTINCT " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = " + str(searchval)

    print("Validate Field SQL = " + qval_sql)

    try:
        sql_val = do_sql(qval_sql, key=DEBUG, earl=EARL)
        # print("sql_val = " + str(sql_val))
        if sql_val is not None:
            row = sql_val.fetchone()
            if row is not None:
                return row[0]
            else:
                if keytype == "char":
                    return ""
                else:
                    return 0

        else:
            if keytype == "char":
                return ""
            else:
                return 0

    except Exception as e:
        print(e)


def fn_check_duplicates(searchval, keyfield, retfield, table, testval, keytype):
    if keytype == "char":
        qval_sql = "SELECT " + retfield + " FROM " + table + " WHERE " \
                   + keyfield + " = '" + str(searchval) + "' AND " + retfield \
                   + " != " + str(testval)
    elif keytype == "integer":
        qval_sql = "SELECT " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = " + searchval \
                   + " AND " + retfield + " != " + str(testval)

    print(qval_sql)

    try:
        sql_val = do_sql(qval_sql, key=DEBUG, earl=EARL)
        if sql_val is not None:
            row = sql_val.fetchone()
            if row == None:
                return 0
            else:
                return row[0]
        else:
            return 0

    except Exception as e:
        print(e)
        return e


def fn_convert_date(date):
    if date != "":
        ndate = datetime.strptime(date, "%m/%d/%Y")
        retdate = datetime.strftime(ndate, "%m/%d/%Y")
        # retdate = datetime.strftime(ndate, "%Y-%m-%d")
    else:
        retdate = None

    # print(retdate)
    return retdate


def fn_format_phone(phone):
    if phone != "":
        v =  phone[1:4]+phone[6:9]+phone[10:14]
        return v
    else:
        return ""


# def do_sql(sql, key, earl):
#
#     print("SQL = " + sql)
#     # print(key)
#     # print(earl)
#
#     cursor = connections[earl].cursor()
#     try:
#         if key == "test":
#             print(sql)
#         else:
#             print(key)
#             cursor.execute(sql)
#             objects = cursor.fetchall()
#
#             if objects is not None:
#
#                 if isinstance(object, tuple):
#                     print("!")
#                     for o in objects:
#                         print(o[0])
#                         return o[0]
#                 else:
#                     print(type(objects))
#             else:
#                 print("do_sql returned nothing")
#                 return 0
#
#
#     except Exception as e:
#         print(e.message)
#         return e

def do_sql2(sql, args):

    print(EARL)
    print(INFORMIX_EARL_TEST)
    print(sql)
    print(args)

    # cursor = connections[EARL].cursor()
    # cursor.execute(sql, args)

    engine.execute(sql, args)


    # cursor.close()
    # objects = cursor.fetchall()
    # if objects is not None:
    #     print objects
    #     for o in objects:
    #         print(o[0])
    #         print(o[1])
    #         print(o[2])
    #         print(o[3])
    #         return o[0]
    #     else:
    #         return 0

# def do_sql3(sql, args):
#
#     engine.execute(sql, args)



# if __name__ == "__main__":
#     args = parser.parse_args()
#     test = args.test
#     database = args.database
#
#     if not database:
#         print "mandatory option missing: database name\n"
#         parser.print_help()
#         exit(-1)
#     else:
#         database = database.lower()
#
#     if database != 'cars' and database != 'train':
#         print "database must be: 'cars' or 'train'\n"
#         parser.print_help()
#         exit(-1)
#
#     sys.exit(main())
