import os
import sys
import csv
from datetime import datetime
import time
from time import strftime
import awscli
# import botocore
# import boto3
# from botocore.exceptions import ClientError
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler
from sqlalchemy import text

# from aws import fn_upload_file

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
from handshake_sql import HANDSHAKE_QUERY
from aws_boto import fn_upload_aws_file

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

# def main():


def fn_build_csv():
    database = 'train'   # I think I will set this in the other module


    # set start_time in order to see how long script takes to execute
    # start_time = time.time()
    ##########################################################################
    # development server (bng), you would execute:
    # ==> python buildcsv.py --database=train --test
    # production server (psm), you would execute:
    # ==> python buildcsv.py --database=cars
    # without the --test argument
    ##########################################################################

    # # set date and time to be added to the filename
    datestr = datetime.now().strftime("%Y%m%d")
    # print(datestr)

    # set date and time to be added to the archive filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # print(datetimestr)

    # Defines file names and directory location
    handshakedata = ('{0}users.csv'.format(
         settings.HANDSHAKE_CSV_OUTPUT))
    print("Handshakedata = " + handshakedata)
    # print (settings.HANDSHAKE_CSV_OUTPUT)

    # set archive directory
    archived_destination = ('{0}_users-{1}.csv'.format(
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
            # session = get_session(EARL)
            # # # Archive
            # # Check to see if file exists, if not send Email
            # if os.path.isfile(handshakedata) != True:
            #     # there was no file found on the server
            #     SUBJECT = '[Handshake Application] failed'
            #     BODY = "There was no .csv output file to move."
            #     # sendmail(
            #     #     settings.ADP_TO_EMAIL,settings.ADP_FROM_EMAIL,
            #     #     BODY, SUBJECT
            #     # )
            #     # fn_write_log("There was no .csv output file to move.")
            #     print("There was no .csv output file to move.")
            # else:
            #     # rename and move the file to the archive directory
            #     shutil.copy(handshakedata, archived_destination)

        #--------------------------
        # Create the csv file
        # Write header row
        print('about to write header')
        # with open("handshakedata.csv", 'w') as file_out:
        with open(handshakedata, 'w') as file_out:
            print ("Opened handshake data location")
            csvWriter = csv.writer(file_out)
            csvWriter.writerow(
                ["email_address", "username", "auth_identifier" ,
                "card_id",
                 "first_name", "last_name", "middle_name",
                 "preferred_name",
                 "school_year_name",
                 "primary_education:education_level_name",
                 "primary_education:cumulative_gpa",
                 "primary_education:department_gpa",
                 "primary_education:primary_major_name",
                 "primary_education:major_names",
                 "primary_education:minor_names",
                 "primary_education:college_name",
                 "primary_education:start_date",
                 "primary_education:end_date",
                 "primary_education:currently_attending",
                 "campus_name", "opt_cpt_eligible", "ethnicity",
                 "gender",
                 "disabled", "work_study_eligible", "system_label_names",
                 "mobile_number", "assigned_to_email_address", "athlete",
                 "veteran", "hometown_location_attributes:name",
                 "eu_gdpr_subject"])
        file_out.close()
        print(' write header')
        # Query CX and start loop through records
        # print(HANDSHAKE_QUERY)

        #______****************************************
        # WHEN I MAKE THE DATABASE CALL, IT MESSES UP THE BOTO3 CLIENT CALL??
        # data_result = do_sql(HANDSHAKE_QUERY, key=DEBUG, earl=EARL)
        # engine = get_engine(EARL)  # do_sql calls get engine
        # data_result = engine.execute(HANDSHAKE_QUERY)
        # I have tried get_engine, execute,. get_session, execute
        # I have confirmed it is NOT the write to file process that is the problem
        # I have tried session.close() and session.commit() and session.expire_all()
        # still same error

        # session = get_session(EARL)
        # data_result = session.execute(HANDSHAKE_QUERY)
        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(HANDSHAKE_QUERY)


        # Causes the error 10 = no child process
        #______****************************************

        ret = list(data_result.fetchall())
        if ret is None:
            print("Data missing")
        #     # fn_write_log("Data missing )
        else:
            print("Data found")
            with open(handshakedata, 'a') as file_out:
                csvWriter = csv.writer(file_out)
                for row in ret:
                     csvWriter.writerow(row)
            file_out.close()
        engine.close()
        engine.dispose()
        EARL.dispose()


        file_date = time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(handshakedata)))
        print("Date of file = " + file_date)
        bucket_name = settings.HANDSHAKE_BUCKET
        object_name = (datestr + '_users.csv')
        file_name = '/data2/www/data/handshake/users.csv'
        remote_folder = settings.HANDSHAKE_S3_FOLDER
        key_name = remote_folder + '/' + object_name
        # print('AWSCLI Data Path = ' + str(awscli._awscli_data_path))

        # print("Waiting for session to clear")
        # time.sleep(30)
        # # for some reason, the aws.py creates the client, but this won't
        # client = boto3.client('s3')
        # print("Client = " + str(client))  # returns <botocore.client.S3 object at 0x7fe83f038d90>
        # # THIS WORKS DO NOT LOSE!
        # print("Upload will use: " + file_name + ", " + bucket_name + ", " + key_name)
        # # client.upload_file(Filename='20190404_users.csv',
        # #                      Bucket='handshake-importer-uploads',
        # #                      Key='importer-production-carthage/20190404_users.csv')
        #
        # # REPLACE WITH
        # # client.upload_file(Filename=file_name, Bucket=bucket_name, Key=key_name)
        #
        #
        # # I want to call the function in aws.py from here, but it returns
        # # error 10 - No Child Processes...
        # # I suspect it is because the write process above has not released
        # # rights to the csv file, but that is a guess


    except Exception as e:
    #         # Use this for final version
    #         # logging.error("Error in handshake buildcsv.py, Error = " +
    #         e.message)
    #
    #         # Test with this then remove, use the standard logging mechanism
    #         fn_write_error("Error in handshake buildcsv.py, Error = " +
    #         e.message)
        print("Error in handshake buildcsv.py, Error = " + e.message)
    #     # finally:
    #     #     logging.shutdown()


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
