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
from djequis.adp.aarec import fn_archive_address
from djequis.adp.utilities import fn_validate_field
# from djzbar.utils.informix import do_sql
from djequis.adp.utilities import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
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
EARL = "default"
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
# engine = get_engine(EARL)

def fn_process_idrec(carth_id, file_number, fullname, lastname, firstname, middlename,
        addr_line1, addr_line2, addr_line3, city, st, zip, ctry, ctry_cod, ss_no, phone,
        decsd, eff_date):

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
        q_update_id_rec = '''
                    update id_rec set fullname = '{0}',
                    lastname = '{1}', firstname = '{2}',
                    middlename = '{3}', ss_no = '{4}',
                    decsd = "N", upd_date = '{5}',
                    ofc_add_by = "HR"
                    where id = {6}
                '''.format(fullname, lastname, firstname,
                       middlename, ss_no, eff_date,
                       carth_id)
        # logger.info("Update id_rec table");

        x = do_sql(q_update_id_rec, key=DEBUG, earl=EARL)
        print(x)

    except Exception as err:
        print(err.message)
        return (err.message)
        logger.error(err, exc_info=True)


    try:
        #     # also need to deal with address changes
        #     # Search for existing address record
        q_check_addr = '''
                    SELECT id, addr_line1, addr_line2, addr_line3, city,
                        st, zip, ctry
                    From id_rec
                    Where id = {0}
                        '''.format(carth_id)
        logger.info("Select address info from id_rec table");
        sql_id_address = do_sql(q_check_addr, key=DEBUG, earl=EARL)
        addr_result = sql_id_address
        print(addr_result)

        if addr_result == None:  # No person in id rec? Should never happen
            logger.info('Employee not in id rec for id number {0}'.format(carth_id));
            print("Employee not in id rec for id number " + carth_id)
            # "carth_id"]))

        # Update ID Rec and archive aa rec
        elif addr_result[1].strip() != addr_line1 \
            or addr_result[2].strip() != addr_line2 \
            or addr_result[3].strip() != addr_line3 \
            or addr_result[4].strip() != city \
            or addr_result[5].strip() != st \
            or addr_result[6].strip() != zip \
            or addr_result[7].strip() != ctry_cod:

            print("Update: no match in ID_REC on " + addr_result[1])  #

        else:
            print(addr_result[1])

    except Exception as err:
        print(err.message)
        logger.error(err, exc_info=True)
        return (err.message)


    try:
        # Compare ADP address to CX address
        # query works - 05/30/18
        q_update_id_rec_addr = '''
                         update id_rec set addr_line1 = '{0}',
                              addr_line2 = '{1}', addr_line3 = '{2}',
                              city = '{3}', st = '{4}', zip = '{5}',
                              ctry = '{6}'
                         where id = {7}
                              '''.format(addr_line1, addr_line2,
                                  addr_line3, city, st, zip, ctry_cod,
                                  carth_id)
        print(q_update_id_rec_addr)
        # logger.info("Update address in id_rec table");
        do_sql(q_update_id_rec_addr, key=DEBUG, earl=EARL)
    except Exception as err:
        logger.error(err, exc_info=True)
        return (err.message)

        #########################################################
        # Routine to deal with aa_rec
        #########################################################
        # now check to see if address is a duplicate in aa_rec
        # find max start date to determine what date to insert
        # insert or update as needed

    # fn_archive_address(carth_id, fullname, addr_line1, addr_line2,
    #             addr_line3, city, st, zip, ctry_cod)


            # return "x"



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