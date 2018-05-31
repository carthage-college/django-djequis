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
from djequis.adp.utilities import fn_validate_field
from djzbar.utils.informix import do_sql
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
EARL = INFORMIX_EARL_TEST
# else:
    # this will raise an error when we call get_engine()
    # below but the argument parser should have taken
    # care of this scenario and we will never arrive here.
#    EARL = None
# establish database connection
engine = get_engine(EARL)

def fn_process_idrec(carth_id, fullname, lastname, firstname, middlename,
        addr_line1, addr_line2, addr_line3, city, st, zip, ctry, ss_no, phone,
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

        ##########################################################
        # Determine if record exists to avoid duplicates
        ##########################################################
        v_id = fn_validate_field(carth_id, "id", "id", "id_rec", "integer")
        print(v_id)

        if v_id == "":
            # In the initial scope, there should be no case where we insert
            # a new record into id_rec - HR begins in CX and creates the record
            # to obtain an ID#.
            # If this changes...Insert and get back the new ID#
            # Insert or update as needed to ID_rec
            # If insert then include address as new
            # Query works = 05/30/18
            # q_insert_id_rec = '''
            #     INSERT INTO id_rec
            #         (id, fullname, lastname, firstname, middlename, addr_line1,
            #         addr_line2, addr_line3, city, st, zip, ctry, AA, ss_no,
            #         phone, decsd, upd_date, ofc_add_by)
            #     VALUES({0},"{1}","{2}","{3}","{4}",
            #     "{5}","{6}","{7}","{8}","{9}","{10}","{11}","PERM","{12}",
            #     "{13}","N","{14}","HR")
            #     '''.format(carth_id, fullname, lastname, firstname,
            #            middlename, addr_line1, addr_line2,
            #            addr_line3, city, st, zip, ctry, ss_no, phone, eff_date)
            # print(q_insert_id_rec)
            # logger.info("Inserted into id_rec table");
            # do_sql(q_insert_id_rec, key=DEBUG, earl=EARL)
            SUBJECT = 'No matcining ID in id_rec - abort and email HR'
            BODY = 'No matching ID in id_rec, process aborted. Name = {0}, \
                                  ADP File = {1}'.format(row["payroll_name"], \
                                                         row["file_number"])
            sendmail(settings.ADP_TO_EMAIL, settings.ADP_FROM_EMAIL,
                     BODY, SUBJECT
                     )
            logger.error('There was no matching ID in id_Rec table, row \
                                       skipped. Name = {0}, \
                                       ADP File = {1}'.format(
                row["payroll_name"], \
                row["file_number"]))
        else:
            # For update, handle demographics and address separately
            # This sql works 5/30/18
            try:
                q_update_id_rec = '''
                            update id_rec set fullname = "{0}",
                            lastname = "{1}", firstname = "{2}",
                            middlename = "{3}", ss_no = "{4}", 
                            decsd = "N", upd_date = "{5}", 
                            ofc_add_by = "HR"
                            where id = {6}
                        '''.format(fullname, lastname, firstname,
                               middlename, ss_no, eff_date,
                               carth_id)
                print(q_update_id_rec)
                logger.info("Update id_rec table");
                # do_sql(q_update_id_rec, key=DEBUG, earl=EARL)
            except Exception as err:
                logger.error(err, exc_info=True)
                return (err.message)

            try:
                # also need to deal with address changes
                # Search for existing address record
                q_check_addr = '''
                            SELECT id, addr_line1, addr_line2, addr_line3, city, 
                                st, zip, ctry 
                            From id_rec 
                            Where id = {0}
                                '''.format(carth_id)
                # print(q_check_addr)
                logger.info("Select address info from id_rec table");
                sql_id_address = do_sql(q_check_addr, earl=EARL)
                addr_result = sql_id_address.fetchone()
                if addr_result == None:  # No person in id rec? Should never happen
                    logger.info("Employee not in id rec for id number {0}".format(
                        carth_id));
                    # print("Employee not in id rec for id number {0}".format(row[
                    # "carth_id"]))


            # Update ID Rec and archive aa rec
                elif addr_result[1].strip() != addr_line1 \
                    or addr_result[2].strip() != addr_line2 \
                    or addr_result[3].strip() != addr_line3 \
                    or addr_result[4].strip() != city \
                    or addr_result[5].strip() != st \
                    or addr_result[6].strip() != zip \
                    or addr_result[7].strip() != ctry:
                    # print("Update: no match in ID_REC on " + addr_result[1])  #

            except Exception as err:
                logger.error(err, exc_info=True)
                return (err.message)


            try:
                # Compare ADP address to CX address
                # query works - 05/30/18
                q_update_id_rec_addr = '''
                                 update id_rec set addr_line1 = "{0}",
                                      addr_line2 = "{1}", addr_line3 = "{2}",
                                      city = "{3}", st = "{4}", zip = "{5}", 
                                      ctry = "{6}" 
                                 where id = {7}
                                      '''.format(addr_line1, addr_line2,
                                          addr_line3, city, st, zip, ctry,
                                          carth_id)
                print(q_update_id_rec_addr)
                logger.info("Update address in id_rec table");
                # do_sql(q_update_id_rec_addr, key=DEBUG, earl=EARL)
            except Exception as err:
                logger.error(err, exc_info=True)
                return (err.message)

                #########################################################
                # Routine to deal with aa_rec
                #########################################################
                # now check to see if address is a duplicate in aa_rec
                # find max start date to determine what date to insert
                # insert or update as needed
                fn_archive_address(carth_id, fullname, addr_line1, addr_line2,
                        addr_line3, city, st, zip, ctry)


        # return "x"

    except Exception as e:
        print(e)


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