import string
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


######################################################
#  START HERE
######################################################
######################################################
# Dates are an issue to resolve
# Need to see if there is a record of the same type (PERM) and if so
# add an end date
# ID, AA and Start date should serve as a key of sorts, and if there is
# another record with the same start date, it will throw Duplicate key error.

# So in addition to seeing if the same address is in the database, also look
# for existing record with same aa type and find its start and stop dates.
# Add End Date to previous record because we would be
# creating a new alternate address

# Scenario 1 -  No aa_rec record exists:   Insert only
# Scenario 2 -  aa_rec is a close match of new data - update
# Scenario 3 -  aa_rec data exists but does not match,
#    end date old record and insert new
######################################################

def archive_address(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry):
  # try

    #################################
    #  See if there is already an Archive record
    #################################

    q_check_aa_adr = '''SELECT id, aa, aa_no, beg_date, line1, line2, line3, 
                        city, st, zip, ctry 
                        From aa_rec 
                        Where id = {0}
                        and aa in ('PERM','PREV','SCND')
                        and end_date is null
                        '''.format(id)
    sql_id_address = do_sql(q_check_aa_adr, earl=EARL)
    addr_result = sql_id_address.fetchone()
    print(q_check_aa_adr)
    print("Addr Result = ")
    print(addr_result)
    # logger.info("Select address info from id_rec table");

    #################################
    #  Find the max start date of all PREV entries with a null end date
    #################################

    q_check_aa_date = '''SELECT max(beg_date), ID, aa, line1, end_date
                                   as date_end
                                   From aa_rec 
                                   Where id = {0}
                                   and aa = 'PREV'
                                   and end_date is null
                                   group by id, aa, end_date, line1
                                   '''.format(id)
    #                       '''.format(row["carth_id"])
    print(q_check_aa_date)
    # logger.info("Select address info from id_rec table");
    sql_date = do_sql(q_check_aa_date, earl=EARL)
    date_result = sql_date.fetchone()
    #print date_result

    #################################
    # Define date variables
    #################################
    if date_result == None:  #No aa rec found
        a1 = ""
        max_date = datetime.now().strftime("%Y/%m/%d")
    # Make sure dates don't overlap
    else:
        print(date_result)
        max_date = date.strftime(date_result[0],"%Y/%m/%d")
        a1 = date_result[3]

    print("A1 = " + a1 )
    print("Max date = " + str(max_date))
    print("Now = " + str(datetime.now()))


    # Scenario 1
    # This means that the ID_Rec address will change
    # but nothing exists in aa_rec, so we will only insert as 'PREV'
    if addr_result == None:  # No address in aa rec?
          print("No existing record - Insert only")
          # call function to insert record
          fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, max_date)

    # Scenario 2
    # if record found in aa_rec, then we will need more options
    # Find out if the record is an exact match with another address
    # Question is, what is enough of a match to update rather than insert new?
    # id, fullname, addr1, addr2, addr3, cty, st, zp, ctry
    # (1003664, 'PREV', 158, datetime.date(2010, 2, 2),
    # '15008 Lost Canyon Ct.#102', '', '', 'Woodbridge', 'VA', '22191', 'USA')
    elif addr_result[4] == addr1 \
         and addr_result[9] == zp:
        # and addr_result[7] == cty \
        # and addr_result[8] == st \
        # and addr_result[10] == ctry:
        # or addr_result[5] == addr2 \
        # or addr_result[6] == addr3 \

          #################################
          # Match found then we are UPDATING only....
          #################################
        fn_update_aa(addr_result[0],addr_result[1],addr_result[2], fullname,
              addr_result[4],addr_result[5],addr_result[6],addr_result[7],
              addr_result[8], addr_result[9],addr_result[10],addr_result[3])

        print("An Address exists and matches new data - Update new")

    # to avoid overlapping dates
    # Scenario 3 - AA Rec exists but does not match new address.
    # End old, insert new
    else:
        if max_date >= str(datetime.now()):
            beg_date = max_date  # add one day...
        else:
            beg_date = datetime.now().strftime("%m/%d/%Y")

        fn_end_date_aa(addr_result[0],addr_result[2],fullname,addr_result[3],
                    datetime.now().strftime("%m/%d/%Y"))
        fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, beg_date)

        print("An Address exists but does not match - end current, insert new")

    return "Success"

#    except Exception as e:

###################################################
# SQL Functions
###################################################
def fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, beg_date):
    q_insert_aa = '''INSERT INTO aa_rec(id, aa, beg_date, peren, end_date,
                         line1, line2, line3, city, st, 
                         zip, ctry, phone, phone_ext, ofc_add_by, 
                         cell_carrier, opt_out)
                      VALUES
                         ({0},{1},{2},{3},{4},
                         {5},{6},{7},{8},{9},
                         {10},{11},{12},{13},{14},
                         {15},{16})
                         '''.format(id, "PERM", beg_date, "N", "",
                                    addr1, addr2, addr3, cty, st,
                                    zp, ctry, "", "", "HR",
                                    "", "")
    # logger.info("insert address into aa_rec table");
    # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
    # insert_result = sql_aa_insert.fetchone(
    # print(q_insert_aa)
    print("insert aa completed")

def fn_update_aa(id, aa, aanum, fllname, add1, add2, add3, cty, st, zip, ctry, begdate):
    q_update_aa = '''update aa_rec 
                      set line1 = "{4}",
                      line2 = "{5}",
                      line3 = "{6}",
                      city = "{8}",
                      st = "{9}",
                      zip = "{10}",
                      ctry = "{11}"  
                      where aa_no = {2}
                      '''.format(id, aa, aanum ,fllname, add1, add2, add3,
                                 begdate, cty, st, zip, ctry)
    # logger.info("update address info in aa_rec table");
    # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
    # insert_result = sql_aa_insert.fetchone(
    # print(q_update_aa)
    print("update aa completed")


def fn_end_date_aa(id, aa_num, fullname, begdate, enddate):

        q_update_aa = '''update aa_rec 
                          set end_date = {4}
                          where id = {0}
                          and aa_no = {1}
                          and beg_date = {3}
                          '''.format(id, aa_num, fullname, begdate, enddate)
        # logger.info("update address info in aa_rec table");
        # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
        # insert_result = sql_aa_insert.fetchone(
        # print(q_update_aa)
        print("end Date aa completed")

    # print(max_date)


def fn_set_cell_phone(phone, id, fullname):
    q_check_cell = '''SELECT aa_rec.aa, aa_rec.id, aa_rec.phone, aa_rec.aa_no, 
        aa_rec.beg_date 
        FROM aa_rec 
        WHERE aa_rec.id = {0} AND aa_rec.aa = 'CELL' AND aa_rec.end_date is null
            '''.format(id)

    sql_cell = do_sql(q_check_cell, earl=EARL)
    cell_result = sql_cell.fetchone()
    if cell_result == None:
        print("No Cell")
    else:
        print(cell_result[2])
        if cell_result[2] == phone:
            print("match " + fullname)





# print(e)


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
