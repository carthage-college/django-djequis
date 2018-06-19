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
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djzbar.settings import INFORMIX_EARL_SANDBOX

from djtools.fields import TODAY

# Imports for additional modules and functions written as part of this project
from djequis.adp.aarec import fn_archive_address
from djequis.adp.utilities import fn_validate_field

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
#     EARL = INFORMIX_EARL_PROD
# elif database == 'train':
#     EARL = INFORMIX_EARL_TEST
# elif database == 'sandbox':
EARL = INFORMIX_EARL_SANDBOX
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
    #EARL = None
# establish database connection
engine = get_engine(EARL)

def fn_process_idrec(carth_id, file_number, fullname, lastname, firstname, middlename,
        addr_line1, addr_line2, addr_line3, city, st, zip, ctry, ctry_cod, ss_no, phone,
        decsd, eff_date):
    print("Start ID Rec Processing")
    # write out the .sql file
    scr = open("apdtocx_output.sql", "a")

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
        q_update_id_rec = ('''UPDATE id_rec SET fullname = ?, lastname = ?, 
            firstname = ?, middlename = ?, ss_no = ?, decsd = 'N', 
            upd_date = ?, ofc_add_by = 'HR' 
            WHERE id = ?''')

        q_update_id_args = (fullname, lastname, firstname, middlename, ss_no, eff_date,
                       carth_id)
        # print(q_update_id_rec)
        # print(q_update_id_args)
        logger.info("Update id_rec table");
        engine.execute(q_update_id_rec, q_update_id_args)
    except Exception as err:
        print(err.message)
        return (err.message)
        logger.error(err, exc_info=True)

    try:
        # also need to deal with address changes
        # Search for existing address record
        if ctry_cod != '':
            cntry = fn_validate_field(ctry_cod, 'ctry', 'ctry', 'ctry_table', 'char')
            #print("Valid Country Code = " + cntry)
            #print(" In Check Address")
            q_check_addr = '''
                        SELECT id, addr_line1, addr_line2, addr_line3, city,
                            st, zip, ctry
                        FROM id_rec
                        WHERE id = {0}
                            '''.format(carth_id)
            addr_result = do_sql(q_check_addr, key=DEBUG, earl=EARL)
            scr.write(q_check_addr + '\n');
            logger.info("Get address info from id_rec table for comparision");
            row = addr_result.fetchone()
            # x = str(row[1]).rstrip()
            # print("Address result row = " + x)
            if str(row[0]) == '0' or str(row[0]) == '':  # No person in id rec? Should never happen
            #     # logger.info('Employee not in id rec for id number {0}'.format(carth_id));
                 print("Employee not in id rec for id number " + carth_id)

            # Update ID Rec and archive aa rec
            elif (row[1].strip() != addr_line1
                or row[2].strip() != addr_line2
                or row[3].strip() != addr_line3
                or row[4].strip() != city
                or row[5].strip() != st
                or row[6].strip() != zip
                or row[7].strip() != ctry_cod):

                print("Update: no match in ID_REC on " + row[1])  #

                q_update_id_rec_addr = ('''UPDATE id_rec SET addr_line1 = ?,
                     addr_line2 = ?, addr_line3 = ?, city = ?, st = ?, zip = ?,
                     ctry = ? WHERE id = ?''')
                q_update_id_addr_args = (addr_line1, addr_line2, addr_line3, city, st,
                                        zip, cntry, carth_id)

                #print(q_update_id_rec_addr)
                #print(q_update_id_addr_args)
                engine.execute(q_update_id_rec_addr, q_update_id_addr_args)
                scr.write(q_update_id_rec_addr + '\n');
                #########################################################
                # Routine to deal with aa_rec
                #########################################################
                # now check to see if address is a duplicate in aa_rec
                # find max start date to determine what date to insert
                # insert or update as needed
                fn_archive_address(carth_id, fullname, addr_line1, addr_line2,
                             addr_line3, city, st, zip, cntry)
            else:
                print("No Change " + row[1])
        elif cntry is None:
            print("invalid country code" + ctry_cod)

    except Exception as err:
        print(err.message)
        logger.error(err, exc_info=True)
        return (err.message)
    finally:
        logging.shutdown()


