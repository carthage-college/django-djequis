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
from djequis.adp.utilities import fn_convert_date
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

def fn_archive_address(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry):
  # try

    #################################
    #  See if there is already an Archive record
    #################################

    q_check_aa_adr = '''SELECT id, aa, aa_no, beg_date, line1, line2, line3, 
                        city, st, zip, ctry 
                        FROM aa_rec 
                        WHERE id = {0}
                        AND aa in ('PERM','PREV','SCND')
                        AND end_date is null
                        '''.format(id)
    sql_id_address = do_sql(q_check_aa_adr, key=DEBUG, earl=EARL)
    addr_result = sql_id_address.fetchone()

    print(q_check_aa_adr)
    print("Addr Result = " + str(addr_result))
    if addr_result is None:
        found_aa_num = 0
    else:
        found_aa_num = addr_result[2]
    print(found_aa_num)
    # logger.info("Select address info from id_rec table");

    #################################
    #  Find the max start date of all PREV entries with a null end date
    #################################

    q_check_aa_date = '''SELECT MAX(beg_date), ID, aa, line1, end_date
                                   AS date_end
                                   FROM aa_rec 
                                   Where id = {0}
                                   AND aa = 'PREV'
                                   AND end_date is null
                                   GROUP BY id, aa, end_date, line1
                                   '''.format(id)
    print(q_check_aa_date)
    # logger.info("Select address info from id_rec table");
    sql_date = do_sql(q_check_aa_date, key=DEBUG, earl=EARL)
    date_result = sql_date.fetchone()
    print(date_result)

    #################################
    # Define date variables
    #################################
    if found_aa_num == 0 or date_result is None:  #No aa rec found
        a1 = ""
        max_date = datetime.now().strftime("%m/%d/%Y")
    # Make sure dates don't overlap
    else:
        max_date = date.strftime(date_result[0],"%m/%d/%Y")
        a1 = date_result[3]

    print("A1 = " + a1 )
    print("Max date = " + str(max_date))


    # Scenario 1
    # This means that the ID_Rec address will change
    # but nothing exists in aa_rec, so we will only insert as 'PREV'
    if found_aa_num == 0:  # No address in aa rec?
          print("No existing record - Insert only")
          # call function to insert record
          fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry,
                       datetime.now().strftime("%m/%d/%Y"))

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

        print("An Address exists and matches new data - Update new")
        #################################
        # Match found then we are UPDATING only....
        #################################
        fn_update_aa(addr_result[0],addr_result[1],addr_result[2], fullname,
              addr_result[4],addr_result[5],addr_result[6],addr_result[7],
              addr_result[8], addr_result[9],addr_result[10],addr_result[3])

    # to avoid overlapping dates
    # Scenario 3 - AA Rec exists but does not match new address.
    # End old, insert new
    else:
        if max_date >= str(datetime.now()):
            end_date = max_date
        else:
            end_date = datetime.now().strftime("%m/%d/%Y")

        x = datetime.strptime(end_date, "%m/%d/%Y") + timedelta(days=1)
        beg_date = x.strftime("%m/%d/%Y")

        print("Check begin date = " + beg_date)

        fn_end_date_aa(addr_result[0], found_aa_num, fullname,
                       end_date, 'PREV')
        ######################################################
        # Timing issue here, it tries the insert before the end date
        # entry is fully committed
        # Need to add something to make sure the end date is in place
        # or I get a duplicate error
        #########################################################
        q_check_enddate = '''SELECT aa_no, id, end_date 
                            FROM aa_rec 
                            WHERE aa_no = {0}
                            AND aa = 'PREV'
                                '''.format(found_aa_num)
        q_confirm_enddate = do_sql(q_check_enddate, key=DEBUG, earl=EARL)
        print(q_check_enddate)
        v_enddate = q_confirm_enddate.fetchone()


        if v_enddate is not None:
            fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry,
                     beg_date)
        else:
            print("Failure on insert.  Could not verify enddate of previous")

        print("An Address exists but does not match - end current, insert new")

    return "Success"

#    except Exception as e:

###################################################
# SQL Functions
###################################################
# Query works 06/05/18
def fn_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, beg_date):
    q_insert_aa = '''INSERT INTO aa_rec(id, aa, beg_date, peren, end_date, 
        line1, line2, line3, city, st, zip, ctry, phone, phone_ext, 
        ofc_add_by, cell_carrier, opt_out)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    q_ins_aa_args=(id, "PERM", beg_date, "N", "", addr1, addr2, addr3, cty, st,
                                    zp, ctry, "", "", "HR", "", "")

    engine.execute(q_insert_aa,q_ins_aa_args)
    # logger.info("insert address into aa_rec table");
    print(q_insert_aa)
    print(q_ins_aa_args)
    print("insert aa completed")

# Query works 06/05/18
def fn_update_aa(id, aa, aanum, fllname, add1, add2, add3, cty, st, zip, ctry, begdate):
    q_update_aa = '''update aa_rec 
                      set line1 = ?,
                      line2 = ?,
                      line3 = ?,
                      city = ?,
                      st = ?,
                      zip = ?,
                      ctry = ?  
                      where aa_no = ?'''
    q_upd_aa_args=(add1, add2, add3, cty, st, zip,
                   ctry, aanum)
    # logger.info("update address info in aa_rec table");
    engine.execute(q_update_aa, q_upd_aa_args)

    print(q_update_aa)
    print(q_upd_aa_args)
    print("update aa completed")

# Query works 06/05/18
def fn_end_date_aa(id, aa_num, fullname, enddate, aa):

        q_enddate_aa = '''update aa_rec 
                          set end_date = ?, aa = ?
                          where id = ?
                          and aa_no = ?'''
        q_enddate_aa_args=(enddate, aa, id, aa_num)

        print("Log end date aa for " + fullname)
        # logger.info("update address info in aa_rec table");
        print(q_enddate_aa)
        print(q_enddate_aa_args)

        engine.execute(q_enddate_aa, q_enddate_aa_args)
        print("end Date aa completed")

    # print(max_date)


def fn_set_cell_phone(phone, id, fullname):
    q_check_cell = '''SELECT aa_rec.aa, aa_rec.id, aa_rec.phone, aa_rec.aa_no, 
        aa_rec.beg_date 
        FROM aa_rec 
        WHERE aa_rec.id = {0} AND aa_rec.aa = 'CELL' AND aa_rec.end_date is null
            '''.format(id)

    sql_cell = do_sql(q_check_cell, key=DEBUG, earl=EARL)
    cell_result = sql_cell.fetchone()
    if cell_result == None:
        print("No Cell")
    else:
        print(cell_result[2])
        if cell_result[2] == phone:
            print("match " + fullname)


#########################################################
# Specific function to deal with email in aa_rec
#########################################################
def fn_set_email2(email, id, fullname):
    q_check_email = '''
                  SELECT aa_rec.aa, aa_rec.id, aa_rec.line1, 
                  aa_rec.aa_no, aa_rec.beg_date 
                  FROM aa_rec
                  WHERE aa_rec.id = {0}
                  AND aa_rec.aa = 'EML2' 
                  AND aa_rec.end_date IS NULL
                  '''.format(id)
    print(q_check_email)
    # logger.info("Select email info from aa_rec table");
    try:
        sql_email = do_sql(q_check_email, earl=EARL)
        email_result = sql_email.fetchone()
        if email_result == None:
            print("New Email will be = " + email)
            fnct_insert_aa(id, fullname,
                           email, "", "", "", "", "", "",
                           datetime.now().strftime("%m/%d/%Y"))
            return("New email")
        elif email_result[2] == email:
            return("No email Change")
        else:
            # End date current EML2
            print("Existing email = " + email_result[0])
            fn_end_date_aa(id, "EML2", email_result[2],
                        fullname,
                        datetime.now().strftime("%m/%d/%Y"))
            # insert new
            fnct_insert_aa(id, fullname, email, "", "", "", "", "", "",
                           datetime.now().strftime("%m/%d/%Y"))
            print("New Email will be = " + email)
            return("Updated email")

    except Exception as e:
        print(e)



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
