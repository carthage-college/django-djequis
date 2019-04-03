import os
import sys
import csv
from datetime import datetime
import time
from time import strftime
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler
from sqlalchemy import text

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

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

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from handshake_sql import HANDSHAKE_QUERY

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
    # set start_time in order to see how long script takes to execute
    # start_time = time.time()
    ##########################################################################
    # development server (bng), you would execute:
    # ==> python buildcsv.py --database=train --test
    # production server (psm), you would execute:
    # ==> python buildcsv.py --database=cars
    # without the --test argument
    ##########################################################################

    # set date and time to be added to the filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Defines file names and directory location
    handshakedata = ('{0}handshake.csv'.format(
         settings.HANDSHAKE_CSV_OUTPUT
    ))
    # print (settings.HANDSHAKE_CSV_OUTPUT)
    # set archive directory
    archived_destination = ('{0}handshake-{1}.csv'.format(
        settings.HANDSHAKE_CSV_ARCHIVED, datetimestr
    ))
    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        # if database == 'cars':
        #     EARL = INFORMIX_EARL_PROD
        if database == 'train':
            EARL = INFORMIX_EARL_TEST
        else:
        # this will raise an error when we call get_engine()
        # below but the argument parser should have taken
        # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)
        print("Handshakedata = " + handshakedata)

        #--------------------------
        # Create the csv file
        # Write header row
        # print('about to write header')
        # with open("handshakedata.csv", 'w') as file_out:
        with open(handshakedata, 'w') as file_out:
            print ("Opened handshake data location")
            csvWriter = csv.writer(file_out)
            csvWriter.writerow(
                ["email_address", "username", "auth_identifier" ,"card_id",
                 "first_name", "last_name", "middle_name", "preferred_name",
                 "school_year_name", "primary_education:education_level_name",
                 "primary_education:cumulative_gpa",
                 "primary_education:department_gpa",
                 "primary_education:primary_major_name",
                 "primary_education:major_names",
                 "primary_education:minor_names",
                 "primary_education:college_name",
                 "primary_education:start_date",
                 "primary_education:end_date",
                 "primary_education:currently_attending",
                 "campus_name", "opt_cpt_eligible", "ethnicity", "gender",
                 "disabled", "work_study_eligible", "system_label_names",
                 "mobile_number", "assigned_to_email_address", "athlete",
                 "veteran", "hometown_location_attributes:name",
                 "eu_gdpr_subject"])
        file_out.close()
        # print(' write header')
        # Query CX and start loop through records
        # print(HANDSHAKE_QUERY)
        data_result = do_sql(HANDSHAKE_QUERY, key=DEBUG, earl=EARL)
        # data_result = do_sql(q_get_data, key=DEBUG, earl=EARL)
        ret = list(data_result.fetchall())
        if ret is None:
            print("Data missing")
        #     # fn_write_log("Data missing )
        else:
            print("Data found")
            # print(ret[0][0])
            with open(handshakedata, 'a') as file_out:
            # with open("handshakedata.csv", 'ab') as file_out:
                csvWriter = csv.writer(file_out)
                for row in ret:
                     csvWriter.writerow(row)
            file_out.close()

        # Archive
        # Check to see if file exists, if not send Email
        if os.path.isfile(handshakedata) != True:
            # there was no file found on the server
            SUBJECT = '[Handshake Application] failed'
            BODY = "There was no .csv output file to move."
            # sendmail(
            #     settings.ADP_TO_EMAIL,settings.ADP_FROM_EMAIL,
            #     BODY, SUBJECT
            # )
            # fn_write_log("There was no .csv output file to move.")
            print("There was no .csv output file to move.")
        else:
            # rename and move the file to the archive directory
            shutil.copy(handshakedata, archived_destination)

    except Exception as e:
        # Use this for final version
        # logging.error("Error in handshake buildcsv.py, Error = " + e.message)

        # Test with this then remove, use the standard logging mechanism
        fn_write_error("Error in handshake buildcsv.py, Error = " + e.message)
        print("Error in handshake buildcsv.py, Error = " + e.message)
    # finally:
    #     logging.shutdown()


def fn_write_error(msg):
    # Test with this then remove, use the standard logging mechanism
    # create error file handler and set level to error
    handler = logging.FileHandler(
         '{0}handshake_error.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                                   datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.error(msg)
    handler.close()
    logger.removeHandler(handler)
    logging.shutdown()
    return("Error logged")


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
