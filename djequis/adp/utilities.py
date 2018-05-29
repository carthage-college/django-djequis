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

#########################################################
# Common function to validate that a record exists
#########################################################
def fn_validate_field(searchval, keyfield, retfield, table, keytype):
    print(keytype)
    if keytype == "char":
        qval_sql = "select distinct " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = '" + str(
            searchval) + "'"
    elif keytype == "integer":
        qval_sql = "select distinct " + retfield + " FROM " + table \
                   + " WHERE " + keyfield + " = " + str(searchval)

    # print(qval_sql)

    try:
        sql_val = do_sql(qval_sql, earl=EARL)
        if sql_val != None:
            row = sql_val.fetchone()

            if row == None:
                return ("")
            else:
                return (row[0])
        else:
            return ("")

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
            print("none ...")
            print("New Email will be = " + email)
            fnct_insert_aa(id, fullname,
                           email, "", "", "", "", "", "",
                           datetime.now().strftime("%Y/%m/%d"))
            return("New")
        elif email_result[2] == email:
            print("no change")
            return("No Change")
        else:
            # End date current EML2
            print("Existing email = " + email_result[0])
            fn_end_date_aa(id, "EML2", email_result[2],
                        fullname,
                        email_result[4],
                        datetime.now().strftime("%Y-%m-%d"))
            # insert new
            fnct_insert_aa(id, fullname, email, "", "", "", "", "", "",
                           datetime.now().strftime("%Y/%m/%d"))
            print("New Email will be = " + email)
            return("Update")

    except Exception as e:
        print(e)



#########################################################
# Specific function to insert into aa_rec
#########################################################
def fnct_insert_aa(id, fullname, addr1, addr2, addr3, cty, st, zp, ctry, beg_date):
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
    #scr.write(q_insert_aa + '\n');
    #logger.info("Inserted " + addr1 + "into aa_rec table for " + fullname + ", ID = " + id);
    #sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
    # insert_result = sql_aa_insert.fetchone(
    #print(q_insert_aa)
    print("Inserted " + addr1 + "into aa_rec table for " + fullname + ", ID = " + str(id))

#########################################################
# Specific function to update aa_rec
#########################################################
def fnct_update_aa(id, aa, aanum, fullname, add1, add2, add3, cty, st, zip, ctry, begdate):
    #print("update aa completed")

    q_update_aa = '''update aa_rec 
                      set line1 = "{4}",
                      line2 = "{5}",
                      line3 = "{6}",
                      city = "{8}",
                      st = "{9}",
                      zip = "{10}",
                      ctry = "{11}"  
                      where aa_no = {2}
                      '''.format(id, aa, aanum ,fullname, add1, add2, add3,
                                 begdate, cty, st, zip, ctry)
    #logger.info("Updated " + addr1 + "in aa_rec table for " + fullname + ", ID = " + id);
    # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
    # insert_result = sql_aa_insert.fetchone(
    #print(q_update_aa)
    print("Updated " + add1 + " in aa_rec table for " + fullname + ", ID = " + str(id))

#########################################################
# Specific function to end date a record in aa_rec
#########################################################
def fn_end_date_aa(id, aa_num, addr1, fullname, begdate, enddate):
# print("end Date aa completed")
    q_update_aa = '''update aa_rec 
                      set end_date = {4}
                      where id = {0}
                      and aa_no = {1}
                      and beg_date = {3}
                      '''.format(id, aa_num, fullname, begdate, enddate)
    # logger.info("End dated " + addr1 + "in aa_rec table for " + fullname +
    #  ", ID = " + id);
    # sql_aa_insert = do_sql(q_insert_aa, earl=EARL)
    # insert_result = sql_aa_insert.fetchone(
    # print(q_update_aa)
    print("End dated " + addr1 + " in aa_rec table for " + fullname + ", " +
            "ID = " + str(id))






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