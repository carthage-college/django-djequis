import os
import sys
import csv
from datetime import datetime
import time
from time import strftime
import awscli
import subprocess
# import botocore
# import boto3
# from botocore.exceptions import ClientError
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler
# from sqlalchemy import text


# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections
from djzbar.utils.informix import do_sql
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine, get_session
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
# from handshake_sql import HANDSHAKE_QUERY
from aws_boto import fn_upload_aws_file
from buildcsv import fn_build_csv

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Collect Handshake data for import
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

def main():
    # First archive the old file
    # Next build the new csv
    print("Building the csv")
    ret = fn_build_csv()
    print("Return = " + str(ret))
    time.sleep(60)

    # Then send the csv via AWS
    print("Calling fn_upload_aws_file")
    fn_upload_aws_file(file_name='20190404_users.csv',
                  bucket_name='handshake-importer-uploads',
                  object_name='importer-production-carthage/20190404_users.csv')



    # # set start_time in order to see how long script takes to execute
    # # start_time = time.time()
    # ##########################################################################
    # # development server (bng), you would execute:
    # # ==> python buildcsv.py --database=train --test
    # # production server (psm), you would execute:
    # # ==> python buildcsv.py --database=cars
    # # without the --test argument
    # ##########################################################################
    #
    # # # set date and time to be added to the filename
    # datestr = datetime.now().strftime("%Y%m%d")
    # # print(datestr)
    #
    # # set date and time to be added to the archive filename
    # datetimestr = time.strftime("%Y%m%d%H%M%S")
    # # print(datetimestr)
    #
    # # Defines file names and directory location
    # handshakedata = ('{0}users.csv'.format(
    #      settings.HANDSHAKE_CSV_OUTPUT))
    # print("Handshakedata = " + handshakedata)
    # # print (settings.HANDSHAKE_CSV_OUTPUT)
    #
    # # set archive directory
    # archived_destination = ('{0}_users-{1}.csv'.format(
    #     settings.HANDSHAKE_CSV_ARCHIVED, datetimestr
    #     ))
    #
    # try:
    #     # set global variable
    #     global EARL
    #     # determines which database is being called from the command line
    #     # if database == 'cars':
    #     #     EARL = INFORMIX_EARL_PROD
    #     if database == 'train':
    #         EARL = INFORMIX_EARL_TEST
    #     else:
    #         # this will raise an error when we call get_engine()
    #         # below but the argument parser should have taken
    #         # care of this scenario and we will never arrive here.
    #         EARL = None
    #         # establish database connection
    #         # session = get_session(EARL)
    #         # # # Archive
    #         # # Check to see if file exists, if not send Email
    #         # if os.path.isfile(handshakedata) != True:
    #         #     # there was no file found on the server
    #         #     SUBJECT = '[Handshake Application] failed'
    #         #     BODY = "There was no .csv output file to move."
    #         #     # sendmail(
    #         #     #     settings.ADP_TO_EMAIL,settings.ADP_FROM_EMAIL,
    #         #     #     BODY, SUBJECT
    #         #     # )
    #         #     # fn_write_log("There was no .csv output file to move.")
    #         #     print("There was no .csv output file to move.")
    #         # else:
    #         #     # rename and move the file to the archive directory
    #         #     shutil.copy(handshakedata, archived_destination)
    #
    #
    #
    #
    #     #--------------------------
    #     # Create the csv file
    #     # Write header row
    #     print('about to write header')
    #
    # except Exception as e:
    # #         # Use this for final version
    # #         # logging.error("Error in handshake buildcsv.py, Error = " +
    # #         e.message)
    # #
    # #         # Test with this then remove, use the standard logging mechanism
    # #         fn_write_error("Error in handshake buildcsv.py, Error = " +
    # #         e.message)
    #     print("Error in handshake buildcsv.py, Error = " + e.message)
    # #     # finally:
    # #     #     logging.shutdown()
    #

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
