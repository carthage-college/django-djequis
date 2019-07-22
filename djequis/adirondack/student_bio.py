#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import pysftp
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
# from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
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
    Collect adirondack data for import
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

def sftp_upload(upload_filename):
    print("In File Upload")
    # by adding cnopts, I'm authorizing the program to ignore the
    # host key and just continue
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None # ignore known host key checking
    # sFTP connection information for Adironcack
    XTRNL_CONNECTION = {
        'host': settings.ADIRONDACK_HOST,
        'username': settings.ADIRONDACK_USER,
        'password': settings.ADIRONDACK_PASS,
        'port': settings.ADIRONDACK_PORT,
        'cnopts': cnopts
    }
    try:
        print("Make Connection")
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            # change directory
            print("Change Directory at SFTP Site")
            sftp.chdir("test/in/")
            # sftp.chdir("prod/in/")
            print(upload_filename)
            sftp.put(upload_filename, preserve_mtime=True)
                # delete original files from our server
                # os.remove(adirondackfiles)
            # close sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'ADIRONDACK UPLOAD failed'
        BODY = 'Unable to PUT .txt file to adirondack server.\n\n{0}'.format(str(e))
        # sendmail(
        #     settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
        #     BODY, SUBJECT
        # )
        print(BODY)

def main():

    ##########################################################################
    # ==> python buildcsv.py --database=train --test
    # ==> python buildcsv.py --database=cars
    ##########################################################################

    # Defines file names and directory location
    adirondackdata = ('{0}carthage_students.txt'.format(
         settings.ADIRONDACK_TXT_OUTPUT))

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
        #--------------------------
        # Create the txt file
        # Write header row
        # print(adirondackdata)
        with open(adirondackdata, 'w') as file_out:
        # with open("carthage_students.txt", 'w') as file_out:
            csvWriter = csv.writer(file_out, delimiter='|')
            csvWriter.writerow(
                ["STUDENT_NUMBER", "FIRST_NAME", "MIDDLE_NAME",
                 "LAST_NAME", "DATE_OF_BIRTH", "GENDER",
                 "IDENTIFIED_GENDER",  "PREFERRED_NAME",
                 "PERSON_TYPE", "PRIVACY_INDICATOR",  "ADDITIONAL_ID1",
                 "ADDITIONAL_ID2",
                 "CLASS_STATUS", "STUDENT_STATUS", "CLASS_YEAR", "MAJOR",
                 "CREDITS_SEMESTER",
                 "CREDITS_CUMULATIVE", "GPA", "MOBILE_PHONE",
                 "MOBILE_PHONE_CARRIER", "OPT_OUT_OF_TEXT",
                 "CAMPUS_EMAIL", "PERSONAL_EMAIL", "PHOTO_FILE_NAME",
                 "PERM_PO_BOX",
                 "PERM_PO_BOX_COMBO", "ADMIT_TERM", "STUDENT_ATHLETE",
                 "ETHNICITY", "ADDRESS1_TYPE", "ADDRESS1_STREET_LINE_1",
                 "ADDRESS1_STREET_LINE_2", "ADDRESS1_STREET_LINE_3",
                 "ADDRESS1_STREET_LINE_4", "ADDRESS1_CITY",
                 "ADDRESS1_STATE_NAME", "ADDRESS1_ZIP", "ADDRESS1_COUNTRY",
                 "ADDRESS1_PHONE",
                 "ADDRESS2_TYPE", "ADDRESS2_STREET_LINE_1",
                 "ADDRESS2_STREET_LINE_2", "ADDRESS2_STREET_LINE_3",
                 "ADDRESS2_STREET_LINE_4", "ADDRESS2_CITY",
                 "ADDRESS2_STATE_NAME", "ADDRESS2_ZIP", "ADDRESS2_COUNTRY",
                 "ADDRESS2_PHONE",
                 "ADDRESS3_TYPE", "ADDRESS3_STREET_LINE_1",
                 "ADDRESS3_STREET_LINE_2", "ADDRESS3_STREET_LINE_3",
                 "ADDRESS3_STREET_LINE_4", "ADDRESS3_CITY",
                 "ADDRESS3_STATE_NAME", "ADDRESS3_ZIP", "ADDRESS3_COUNTRY",
                 "ADDRESS3_PHONE",
                 "CONTACT1_TYPE", "CONTACT1_NAME",
                 "CONTACT1_RELATIONSHIP",
                 "CONTACT1_HOME_PHONE",
                 "CONTACT1_WORK_PHONE",
                 "CONTACT1_MOBILE_PHONE",
                 "CONTACT1_EMAIL",
                 "CONTACT1_STREET",
                 "CONTACT1_STREET2",
                 "CONTACT1_CITY",
                 "CONTACT1_STATE",
                 "CONTACT1_ZIP",
                 "CONTACT1_COUNTRY",
                 "CONTACT2_TYPE", "CONTACT2_NAME",
                 "CONTACT2_RELATIONSHIP", "CONTACT2_HOME_PHONE",
                 "CONTACT2_WORK_PHONE", "CONTACT2_MOBILE_PHONE",
                 "CONTACT2_EMAIL", "CONTACT2_STREET", "CONTACT2_STREET2",
                 "CONTACT2_CITY", "CONTACT2_STATE", "CONTACT2_ZIP",
                 "CONTACT2_COUNTRY", "CONTACT3_TYPE", "CONTACT3_NAME",
                 "CONTACT3_RELATIONSHIP", "CONTACT3_HOME_PHONE",
                 "CONTACT3_WORK_PHONE", "CONTACT3_MOBILE_PHONE",
                 "CONTACT3_EMAIL", "CONTACT3_STREET", "CONTACT3_STREET2",
                 "CONTACT3_CITY", "CONTACT3_STATE", "CONTACT3_ZIP",
                 "CONTACT3_COUNTRY", "TERM", "RACECODE"])
        file_out.close()

        # print(ADIRONDACK_QUERY)
        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(ADIRONDACK_QUERY)

        ret = list(data_result.fetchall())
        if ret is None:
            SUBJECT = '[adirondack Application] failed'
            BODY = "SQL Query returned no data."
            sendmail(
                settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
                BODY, SUBJECT
            )
        else:
            print("Query successful")
            with open(adirondackdata, 'a') as file_out:
            # with open("carthage_students.txt", 'a') as file_out:
                csvWriter = csv.writer(file_out, delimiter='|')
                encoded_rows = encode_rows_to_utf8(ret)
                for row in encoded_rows:
                    csvWriter.writerow(row)
            file_out.close()

            # send file to SFTP Site..
            # sftp_upload(adirondackdata)

    except Exception as e:

        fn_write_error("Error in adirondack buildcsv.py, Error = " + e.message)
        SUBJECT = '[adirondack Application] Error'
        BODY = "Error in adirondack buildcsv.py, Error = " + e.message
        sendmail(settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
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
