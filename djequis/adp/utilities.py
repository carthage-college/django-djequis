import os
import string
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import datetime, timedelta
import codecs
import time
from time import strftime
import argparse
#import uuid
from sqlalchemy import text
import shutil
#import re
import logging
from logging.handlers import SMTPHandler


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
# elif database == 'sandbox':
EARL = INFORMIX_EARL_SANDBOX
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
engine = get_engine(EARL)

# write out the .sql file
scr = open("apdtocx_output.sql", "a")
# set start_time in order to see how long script takes to execute
start_time = time.time()
# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to info
handler = logging.FileHandler('{0}apdtocx.log'.format(settings.LOG_FILEPATH))
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                              datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)
# create error file handler and set level to error
handler = logging.FileHandler(
    '{0}apdtocx_error.log'.format(settings.LOG_FILEPATH))
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                              datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)
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
    #print("Validate Field SQL = " + qval_sql)
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

#########################################################
# Common function to prevent duplicate entries
#########################################################
def fn_check_duplicates(searchval, keyfield, retfield, table, testval, keytype):
    if keytype == "char":
        qval_sql = "SELECT " + retfield + " FROM " + table + " WHERE " \
                   + keyfield + " = '" + str(searchval) + "' AND " + retfield \
                   + " != " + str(testval)
    elif keytype == "integer":
        qval_sql = "SELECT " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = " + searchval \
                   + " AND " + retfield + " != " + str(testval)
    #print(qval_sql)
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

#########################################################
# Common function to format date for CX
#########################################################
def fn_convert_date(date):
    if date != "":
        ndate = datetime.strptime(date, "%m/%d/%Y")
        retdate = datetime.strftime(ndate, "%m/%d/%Y")
        # retdate = datetime.strftime(ndate, "%Y-%m-%d")
    else:
        retdate = None
    # print(retdate)
    return retdate

#########################################################
# Common function to format phone for CX
#########################################################
def fn_format_phone(phone):
    if phone != "":
        v =  phone[1:4]+phone[6:9]+phone[10:14]
        return v
    else:
        return ""

#########################################################
# Common function to calculate age from ADP birthdate
#########################################################
def fn_calculate_age(bdate):
    # print("Birtdate = " + bdate)
    d_born = datetime.strptime(bdate, '%m/%d/%Y')
    # print(d_born)
    today = date.today()
    # print(today)
    age = today.year - d_born.year - ((today.month, today.day) < (d_born.month, d_born.day))
    # print(age)
    return(age)



# def fn_write_error(msg):
#     logger.error(msg)
#     return("Error logged")
#
# def fn_write_log(msg):
#     logger.info(msg)
#     return("Message logged")
#
# def fn_earl():
#     # print(EARL)
#     return(EARL)


# def fn_send_mail(to, from, subject, message):
#     return(0)
