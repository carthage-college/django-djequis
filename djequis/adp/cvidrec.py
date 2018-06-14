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
#import adp_ftp
import codecs

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
from djequis.adp.utilities import fn_validate_field, fn_check_duplicates #, do_sql, do_sql2
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


def fn_process_cvid(carthid, adpid, ssn, adp_assoc_id):
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to info
    handler = logging.FileHandler(
        '{0}apdtocx.log'.format(settings.LOG_FILEPATH))
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


    try:
        ##############################################################
        # Inserts or updates as needed into cvid_rec
        ##############################################################

        # print(carthid, adpid, ssn, adp_assoc_id)

        # Validate the cx_id
        v_cx_id = fn_validate_field(carthid, "cx_id", "cx_id", "cvid_rec",
                    "integer")
        print("CX_ID = " + str(carthid))
        print("v_CX_ID = " + str(v_cx_id))

        # Should also check for duplicates of the adp_id and associate_id
        # What to do in that case?
        v_adp_match = fn_check_duplicates(adpid, "adp_id", "cx_id", "cvid_rec",
                                 v_cx_id, "char")
        print("Found_ID = " + str(v_adp_match))

        # By definition, associate ID cannot be a duplicate in ADP, but
        # possibility of duplicate might exist in CX
        v_assoc_match = fn_check_duplicates(adp_assoc_id, "adp_associate_id",
                       "cx_id", "cvid_rec", v_cx_id, "char")
        print("Found ID = " + str(v_assoc_match))



        if v_cx_id == 0 and v_assoc_match == 0 and v_adp_match == 0:
            # Insert or update as needed to ID_rec
            # Insert works 06/12/18

            # mydata = ('111', 'Foobar', '1/1/18', None)

            q_insert_cvid_rec = '''INSERT INTO cvid_rec (old_id, old_id_num, 
              adp_id, ssn, cx_id, cx_id_char, adp_associate_id) 
              VALUES (?,?,?,?,?,?,?)'''
            args = (carthid, carthid, adpid, ssn, carthid, carthid, adp_assoc_id)

            print(q_insert_cvid_rec)

            engine.execute(q_insert_cvid_rec, args)
            # scr.write(q_insert_cvid_rec + '\n');
            # logger.info("Inserted into cvid_rec table");
            # do_sql(q_insert_cvid_rec, key=DEBUG, earl=EARL)
            # do_sql2(q_insert_cvid_rec, cv_args)
        elif str(v_cx_id) != v_assoc_match and v_assoc_match != 0:
            print('Duplicate Associate ID found')
        elif str(v_cx_id) != str(v_adp_match) and v_adp_match != 0:
            print('Duplicate ADP ID found')
        else:
            # sql works - 6/12/18
            q_update_cvid_rec = '''UPDATE cvid_rec SET old_id = ?, 
                old_id_num = ?, adp_id = ?, ssn = ?, adp_associate_id = ? 
                WHERE cx_id = ?'''
            args = (carthid, carthid, adpid, ssn, adp_assoc_id, carthid)
            print(q_update_cvid_rec)
            #  logger.info("Update cvid_rec table");
            # do_sql(q_update_cvid_rec, key=DEBUG, earl=EARL)
            engine.execute(q_update_cvid_rec, args)


    except Exception as e:
        print(e)


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test
    database = args.database

    if not database:
        print "mandatory option missing: database name\n"
        parser.print_help()
        exit(-1)
    else:
        database = database.lower()

    if database != 'cars' and database != 'train':
        print "database must be: 'cars' or 'train'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())