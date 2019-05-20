#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import time
from time import strftime
from datetime import datetime
import awscli
import botocore
import boto3
from botocore.exceptions import ClientError
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler

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
from handshake_sql import HANDSHAKE_QUERY

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

def fn_write_error(msg):
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
    fn_clear_logger()
    return("Error logged")

def fn_clear_logger():
    logging.shutdown()
    return("Clear Logger")

def encode_rows_to_utf8(rows):
    encoded_rows = []
    for row in rows:
        try:
            encoded_row = []
            for value in row:
                if isinstance(value, basestring):
                    value = value.decode('cp1252').encode("utf-8")
                encoded_row.append(value)
            encoded_rows.append(encoded_row)
        except Exception as e:
            fn_write_error("Error in encoded_rows routine " + e.message)
    return encoded_rows

def main():
    # It is necessary to create the boto3 client early because the call to
    #  the Informix database will not allow it later.
    client = boto3.client('s3')

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python buildcsv.py --database=train --test
    # production server (psm), you would execute:
    # ==> python buildcsv.py --database=cars
    # without the --test argument
    ##########################################################################

    # set date and time to be added to the filename
    datestr = datetime.now().strftime("%Y%m%d")

    # set date and time to be added to the archive filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Defines file names and directory location
    handshakedata = ('{0}users.csv'.format(
         settings.HANDSHAKE_CSV_OUTPUT))

    # set archive directory
    archived_destination = ('{0}users-{1}.csv'.format(
        settings.HANDSHAKE_CSV_ARCHIVED, datetimestr
        ))

    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        if database == 'cars':
            EARL = INFORMIX_EARL_PROD
        if database == 'train':
            EARL = INFORMIX_EARL_TEST
        else:
            # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None

        # # Archive
        # Check to see if file exists, if not send Email
        if os.path.isfile(handshakedata) != True:
            # there was no file found on the server
            SUBJECT = '[Handshake Application] failed'
            BODY = "There was no .csv output file to move."
            sendmail(
                settings.HANDSHAKE_TO_EMAIL,settings.HANDSHAKE_FROM_EMAIL,
                BODY, SUBJECT
            )
            fn_write_error("There was no .csv output file to move.")
        else:
            # print("Archive test")
            # rename and move the file to the archive directory
            shutil.copy(handshakedata, archived_destination)

        #--------------------------
        # Create the csv file
        # Write header row
        with open(handshakedata, 'w') as file_out:
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
        # Query CX and start loop through records

        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(HANDSHAKE_QUERY)

        ret = list(data_result.fetchall())
        if ret is None:
            SUBJECT = '[Handshake Application] failed'
            BODY = "SQL Query returned no data."
            sendmail(
                settings.HANDSHAKE_TO_EMAIL,settings.HANDSHAKE_FROM_EMAIL,
                BODY, SUBJECT
            )
        else:
            with open(handshakedata, 'a') as file_out:
                csvWriter = csv.writer(file_out)
                encoded_rows = encode_rows_to_utf8(ret)
                for row in encoded_rows:
                    csvWriter.writerow(row)
            file_out.close()

        # Send the file to Handshake via AWS
        bucket_name = settings.HANDSHAKE_BUCKET
        object_name = (datestr + '_users.csv')

        local_file_name = settings.HANDSHAKE_CSV_OUTPUT + 'users.csv'
        remote_folder = settings.HANDSHAKE_S3_FOLDER
        key_name = remote_folder + '/' + object_name

        print("Filename = " + local_file_name + ", Bucket = " + bucket_name + ", Key = " + key_name)
        client.upload_file(Filename=local_file_name, Bucket=bucket_name,
                           Key=key_name)

        # retaws = client.upload_file(Filename=local_file_name,
        #                             Bucket=bucket_name, Key=key_name)
        # print("Return = " + str(retaws))

        # # THIS IS WHAT IT SHOULD LOOK LIKE - IT WORKS DO NOT LOSE!
        # # client.upload_file(Filename='20190404_users.csv',
        # #            Bucket='handshake-importer-uploads',
        # #            Key='importer-production-carthage/20190404_users.csv')

    except Exception as e:

        fn_write_error("Error in handshake buildcsv.py, Error = " + e.message)
        SUBJECT = '[Handshake Application] Error'
        BODY = "Error in handshake buildcsv.py, Error = " + e.message
        sendmail(settings.HANDSHAKE_TO_EMAIL,settings.HANDSHAKE_FROM_EMAIL,
            BODY, SUBJECT)

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
