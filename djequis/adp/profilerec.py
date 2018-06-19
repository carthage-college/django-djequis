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

# django settings for script
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

# from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djzbar.settings import INFORMIX_EARL_SANDBOX

from djtools.fields import TODAY

# Imports for additional modules and functions written as part of this project
from djequis.adp.utilities import fn_validate_field, fn_convert_date, fn_calculate_age

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
# elif database = 'sandbox'
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
handler = logging.FileHandler('{0}apdtocx_error.log'.format(settings.LOG_FILEPATH))
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                              datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fn_process_profile_rec(id, ethnicity, sex, race, birth_date,
        prof_last_upd_date):
    try:
        ##########################################################
        #  Find out if record exists to determine update vs insert
        ##########################################################
        prof_rslt = fn_validate_field(id, "id", "id",
                                      "profile_rec", "integer")
        #print("Prof Result = " + str(prof_rslt))
        # create race dictionary
        racecode = {
            '1': 'WH',
            '2': 'BL',
            '4': 'AS',
            '6': 'AP',
            '9': 'MU'
        }
        race = racecode.get(race)
        # create ethnicity dictionary
        ethnic_code = {
            'Not Hispanic or Latino': 'N',
            'HISPANIC OR LATINO': 'Y'
        }
        is_hispanic = ethnic_code.get(ethnicity)
        #print(is_hispanic)
        age = fn_calculate_age(birth_date)
        #print("Age = " + str(age))
        if prof_rslt is None or prof_rslt == 0:
            # Insert or update as needed
            q_insert_prof_rec = '''
              INSERT INTO profile_rec (id, sex, race, hispanic, birth_date, 
                age, prof_last_upd_date)
              VALUES (?, ?, ?, ?, ?, ?, ?) '''
            q_ins_prof_args=(id, sex, race, is_hispanic, birth_date, age,
                             prof_last_upd_date)
            # print(q_insert_prof_rec)
            # print(q_ins_prof_args)
            engine.execute(q_insert_prof_rec, q_ins_prof_args)
            # scr.write(q_insert_prof_rec + '\n');
            logger.info("Inserted into profile_rec table");
            scr.write(q_insert_prof_rec + '\n');
        else:
            q_update_prof_rec = '''
                       UPDATE profile_rec SET sex = ?,
                           hispanic = ?, race = ?,
                           birth_date = ?, age = ?,
                           prof_last_upd_date = ?
                           WHERE id = ?'''
            q_upd_prof_args = (sex, is_hispanic, race,
                birth_date, age, prof_last_upd_date, id)
            print(q_update_prof_rec)
            print(q_upd_prof_args)
            engine.execute(q_update_prof_rec, q_upd_prof_args)
            # scr.write(q_update_prof_rec + '\n');
            logger.info("Update profile_rec table");

    except Exception as e:
        print(e)
    finally:
        logging.shutdown()