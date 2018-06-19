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
from djzbar.utils.informix import get_engine, get_session
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
session = get_session(EARL)


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
    try:

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
              fn_insert_aa(id, fullname, 'PERM', addr1, addr2, addr3, cty, st, zp, ctry,
                           datetime.now().strftime("%m/%d/%Y"))

        # Scenario 2
        # if record found in aa_rec, then we will need more options
        # Find out if the record is an exact match with another address
        # Question is, what is enough of a match to update rather than insert new?
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
            id, aa_num, fullname, enddate, aa
            fn_end_date_aa(id, found_aa_num, fullname,
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
            print(q_check_enddate)
            q_confirm_enddate = do_sql(q_check_enddate, key=DEBUG, earl=EARL)

            v_enddate = q_confirm_enddate.fetchone()

            print(v_enddate)

            if v_enddate is not None:
                fn_insert_aa(id, fullname, 'PERM', addr1, addr2, addr3, cty, st,
                        zp, ctry, beg_date)
            else:
                print("Failure on insert.  Could not verify enddate of previous")

            print("An Address exists but does not match - end current, insert new")

        return "Success"

    except Exception as e:
        print(e)

###################################################
# SQL Functions
###################################################
# Query works 06/05/18
def fn_insert_aa(id, fullname, aa, addr1, addr2, addr3, cty, st, zp, ctry, beg_date):
    q_insert_aa = '''INSERT INTO aa_rec(id, aa, beg_date, peren, end_date, 
        line1, line2, line3, city, st, zip, ctry, phone, phone_ext, 
        ofc_add_by, cell_carrier, opt_out)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    q_ins_aa_args=(id, aa, beg_date, "N", "", addr1, addr2, addr3, cty, st,
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
    try:
        q_enddate_aa = '''update aa_rec
                          set end_date = ?, aa = ?
                          where id = ?
                          and aa_no = ?'''

        q_enddate_aa_args=(enddate, aa, id, aa_num)

        x = engine.execute(q_enddate_aa, q_enddate_aa_args)
        print(x)

        print("Log end date aa for " + fullname)
        # logger.info("update address info in aa_rec table");
        print(q_enddate_aa)
        print(q_enddate_aa_args)

        print("end Date aa completed")
        return(1)
    except(e):
        return(0)
#########################################################
# Specific function to deal with cell phone in aa_rec
#########################################################
def fn_set_cell_phone(phone, id, fullname):
    q_check_cell = '''SELECT aa_rec.aa, aa_rec.id, aa_rec.phone, aa_rec.aa_no, 
        aa_rec.beg_date
        FROM aa_rec 
        WHERE aa_rec.id = {0} AND aa_rec.aa = 'CELL' AND aa_rec.end_date is null
            '''.format(id)
    print(q_check_cell)
    # logger.info("Select email info from aa_rec table");

    try:
        sql_cell = do_sql(q_check_cell, key=DEBUG, earl=EARL)
        cell_result = sql_cell.fetchone()
        if cell_result is None:
            print("No Cell")
            fn_insert_aa(id, fullname, 'CELL',
                           phone, "", "", "", "", "", "",
                           datetime.now().strftime("%m/%d/%Y"))
            return("New Cell Phone")

        elif cell_result[2] == phone:
            return("No Cell Phone Change")

        else:
            # End date current CELL
            print("Existing cell = " + cell_result[0])
            q_check_end = '''SELECT max(aa_rec.end_date)
                 FROM aa_rec 
                 WHERE aa_rec.id = {0} AND aa_rec.aa = 'CELL' 
                     '''.format(id)
            print(q_check_end)

            sql_end = do_sql(q_check_end, key=DEBUG, earl=EARL)
            end_rslt = sql_end.fetchone()

            # print(datetime.strftime(end_rslt[0], "%m/%d/%Y"))
            # print(datetime.strftime(datetime.now(), "%m/%d/%Y"))
            if end_rslt[0] is None:
                print('END IS NONE')
                enddate = datetime.now().strftime("%m/%d/%Y")
                x = datetime.strptime(enddate, "%m/%d/%Y") + timedelta(days=1)
                begindate = x.strftime("%m/%d/%Y")
                print(begindate)
                print(enddate)
                fn_end_date_aa(id, cell_result[3], fullname, enddate, "CELL")
                fn_insert_aa(id, fullname, 'CELL', phone, "", "", "", "", "", "",
                          begindate)
            elif datetime.strftime(end_rslt[0], "%m/%d/%Y") >= datetime.strftime(datetime.now(), "%m/%d/%Y"):
                # print('END IS ' + str(datetime.strftime(end_rslt[0])))
                # x = datetime.strptime(end_rslt[0], "%m/%d/%Y") + timedelta(days=1)
                x = end_rslt[0] + timedelta(days=1)
                y = end_rslt[0] + timedelta(days=2)
                enddate = x.strftime("%m/%d/%Y")
                begindate = y.strftime("%m/%d/%Y")
                print(enddate)
                print(begindate)
                fn_end_date_aa(id, cell_result[3], fullname, enddate, "CELL")
                fn_insert_aa(id, fullname, 'CELL', phone, "", "", "", "", "", "",
                              begindate)


            print("New cell will be = " + phone)
            return ("Updated cell")


    except Exception as e:
        print(e)

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
            fn_insert_aa(id, fullname, 'EML2',
                           email, "", "", "", "", "", "",
                           datetime.now().strftime("%m/%d/%Y"))
            return("New email")
        elif email_result[2] == email:
            return("No email Change")
        else:
            # End date current EML2
            # End date current CELL
            print("Existing Email = " + email_result[0])
            q_check_end = '''SELECT max(aa_rec.end_date)
                            FROM aa_rec 
                            WHERE aa_rec.id = {0} AND aa_rec.aa = 'EML2' 
                                '''.format(id)
            print(q_check_end)

            sql_end = do_sql(q_check_end, key=DEBUG, earl=EARL)

            end_rslt = sql_end.fetchone()

            if end_rslt[0] is None:
                print('END IS NONE')
                enddate = datetime.now().strftime("%m/%d/%Y")
                x = datetime.strptime(enddate, "%m/%d/%Y") + timedelta(days=1)
                begindate = x.strftime("%m/%d/%Y")
                print(begindate)
                print(enddate)
                fn_end_date_aa(id, email_result[3], fullname, enddate, "EML2")
                fn_insert_aa(id, fullname, 'EML2', email, "", "", "", "", "",
                             "",
                             begindate)
            elif datetime.strftime(end_rslt[0],
                                   "%m/%d/%Y") >= datetime.strftime(
                    datetime.now(), "%m/%d/%Y"):
                x = end_rslt[0] + timedelta(days=1)
                y = end_rslt[0] + timedelta(days=2)
                enddate = x.strftime("%m/%d/%Y")
                begindate = y.strftime("%m/%d/%Y")
                print(enddate)
                print(begindate)
                fn_end_date_aa(id, email_result[3], fullname, enddate, "EML2")
                fn_insert_aa(id, fullname, 'EML2', email, "", "", "", "", "",
                             "",
                             begindate)


    except Exception as e:
        print(e)

def fn_set_schl_rec(id, fullname, phone, ext, loc, room):
    q_check_schl = '''select id, aa_no, beg_date, end_date, line1, line3, 
        phone, phone_ext from aa_rec where id = {0} and aa = "{1}"'''.format(id, "SCHL")

    print(q_check_schl)
    try:
        sql_schl = do_sql(q_check_schl, earl=EARL)
        schl_result = sql_schl.fetchone()
        print(schl_result)

        location = loc + " " + room

        if schl_result is not None:
            if schl_result[4] == fullname and schl_result[5] == location \
                    and schl_result[6] ==  phone and schl_result[7] == ext:
                return("No Change in SCHL in aa_rec")

            else:
                q_update_schl = '''update aa_rec 
                                     set line1 = ?,
                                     line3 = ?,
                                     phone = ?,
                                     phone_ext = ?
                                     where aa_no = ?'''
                q_upd_schl_args = (fullname, location, phone, ext, schl_result[1])
                # logger.info("update address info in aa_rec table");
                engine.execute(q_update_schl, q_upd_schl_args)

                print(q_update_schl)
                print(q_upd_schl_args)
                print("update SCHL completed")

        else:
            print("New SCHL rec will be added ")
            # add location and room?
            loc = ""
            carthphone = ""
            ext = ""
            q_insert_schl = '''INSERT INTO aa_rec(id, aa, beg_date, peren, 
            end_date, 
                 line1, line2, line3, city, st, zip, ctry, phone, phone_ext, 
                 ofc_add_by, cell_carrier, opt_out)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            q_ins_schl_args = (id, "SCHL",  datetime.now().strftime("%m/%d/%Y"),
                "N", "", fullname, "", location, "", "", "", "", carthphone, ext,
                "HR", "", "")

            engine.execute(q_insert_schl, q_ins_schl_args)
            # logger.info("insert address into aa_rec table");
            print("insert SCHL completed")

    except Exception as e:
        print(e)