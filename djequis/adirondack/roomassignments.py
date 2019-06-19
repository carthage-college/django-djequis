#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import pysftp
import pyodbc
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler
# importing required modules
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djzbar.settings import MSSQL_LENEL_EARL
from adirondack_sql import ADIRONDACK_QUERY

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Collect adirondack pictures for import
"""
parser = argparse.ArgumentParser(description=desc)

# Test with this then remove, use the standard logging mechanism
logger = logging.getLogger(__name__)

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

def fn_write_error(msg):
    # create error file handler and set level to error
    handler = logging.FileHandler(
        '{0}adirondack_error.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.error(msg)
    handler.close()
    logger.removeHandler(handler)
    fn_clear_logger()
    return("Error logged")

def fn_clear_logger():
    logging.shutdown()
    return("Clear Logger")

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)

#sFTP fetch (GET) downloads the file from ADP file from server
def file_download():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # External connection information for ADP Application server
    XTRNL_CONNECTION = {
       'host':settings.ADP_HOST,
       'username':settings.ADP_USER,
       'password':settings.ADP_PASS,
       'cnopts':cnopts
    }

    ##########################################################################
    # sFTP GET downloads the CSV file from ADP server and saves
    # in local directory.
    ##########################################################################
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        # try
        sftp.chdir("adp/")
        # Remote Path is the ADP server and once logged in we fetch
        # directory listing
        remotepath = sftp.listdir()
        # Loop through remote path directory list
        for filename in remotepath:
            remotefile = filename
            # set local directory for which the ADP file will be downloaded to
            local_dir = ('{0}'.format(
                settings.ADP_CSV_OUTPUT
            ))
            localpath = local_dir + remotefile
            # GET file from sFTP server and download it to localpath
            sftp.get(remotefile, localpath)
            #############################################################
            # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
            # from sFTP (ADP) server
            #############################################################
            # sftp.remove(filename)
        # except Exception as e:
        # print("Error in adptocx.py, adptocx.csv not found ",
        # fn_write_error("Error in adptocx.py, adptocx.csv not found ",
    sftp.close()



def main():

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python student_pictures.py --database=train --test
    # production server (psm), you would execute:
    # ==> python student_pictures.py --database=cars
    # without the --test argument
    ##########################################################################

    #---------------------------------------------
    # Download the csv file
    #---------------------------------------------

    # set local directory for which the common app file will be downloaded to
    # source_dir = ('{0}'.format(
    #     settings.ADIRONDACK_CSV_OUTPUT
    # ))

    # Defines file names and directory location
    # new_adirondack_file = ('{0}adirondacktocx.csv'.format(
    #     settings.ADIRONDACK_CSV_OUTPUT
    # ))

    # if not test:
    #     file_download()
    # room_assign_file = "roomassignments.txt"
    #---------------------------------------------
    # Read the csv file
    #---------------------------------------------
    with open("roomassignments.txt", 'r') as f:
        d_reader = csv.reader(f, delimiter='|')
        for row in d_reader:
            # print(row)
            # print('--------------------------------------------------')
            carthid = str(row[0])
            building = row[1]
            room = row[2]
            startdate = row[4]
            enddate = row[5]
            term = row[6][:2]
            yr = row[6][2:]
            occupants = row[7]
            action = row[8]

        #---------------------------------------------
        # Insert into stu_serv_rec
        #---------------------------------------------

        # try:
        #     # set global variable
        #     global EARL
        #     # determines which database is being called from the command line
        #     if database == 'cars':
        #         EARL = INFORMIX_EARL_PROD
        #     if database == 'train':
        #         EARL = INFORMIX_EARL_TEST
        #     else:
        #         # this will raise an error when we call get_engine()
        #         # below but the argument parser should have taken
        #         # care of this scenario and we will never arrive here.
        #         EARL = None
        #
        #     # Probably need to validate against CX, avoid duplicate entry
        #     # select from stu_serv_rec where id = 12345 and add_date = 1/1/19 and
        #     # term = and yr = and room = and bldg = ....
            q_validate_stuserv_rec = '''
                          select id, sess, yr, rsv_stat, 
                          intend_hsg, campus, bldg, room, no_per_room, add_date, 
                          bill_code, hous_wd_date 
                          from stu_serv_rec 
                          where id = {0}'''.format(carthid)
            print(q_validate_stuserv_rec)




            q_insert_stuserv_rec = '''
                          INSERT INTO stu_serv_rec (id, sess, yr, rsv_stat, 
                          intend_hsg, campus, bldg, room, no_per_room, add_date, 
                          bill_code, hous_wd_date)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?)'''
            q_insert_stuserv_args = (
                carthid, term, yr, 'R', 'R', 'MAIN', building, room, occupants,
                startdate, 'STD', enddate)
            print(q_insert_stuserv_rec)
            print(q_insert_stuserv_args)
        #     # engine.execute(q_insert_stuserv_rec, q_insert_stuserv_args)
        #
        #     filepath = settings.ADIRONDACK_CSV_OUTPUT



    # except Exception as e:
    #
    #     # fn_write_error("Error in adirondack buildcsv.py, Error = " + e.message)
    #     SUBJECT = '[adirondack Application] Error'
    #     BODY = "Error in adirondack roomassignments.py, Error = " + e.message
    #     # sendmail(settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
    #     #     BODY, SUBJECT)
    #     print(SUBJECT, BODY)


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

    if database != 'cars' and database != 'train' and database != 'sandbox':
        print "database must be: 'cars' or 'train' or 'sandbox'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())
