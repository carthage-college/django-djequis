#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import pysftp
import argparse
import logging
from logging.handlers import SMTPHandler
# prime django
import django
# django settings for script
from django.conf import settings
from django.db import connections
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from adirondack_sql import ADIRONDACK_QUERY
from utilities import fn_write_student_bio_header, \
    fn_encode_rows_to_utf8

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

django.setup()


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
    return "Error logged"


def fn_clear_logger():
    logging.shutdown()
    return "Clear Logger"


def sftp_upload(upload_filename):
    # cnopts authorizes the program to ignore the host key
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # ignore known host key checking
    # sFTP connection information for Adironcack
    XTRNL_CONNECTION = {
        'host': settings.ADIRONDACK_HOST,
        'username': settings.ADIRONDACK_USER,
        'password': settings.ADIRONDACK_PASS,
        'port': settings.ADIRONDACK_PORT,
        'cnopts': cnopts
    }
    try:
        # print("Make Connection")
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            # change directory
            # sftp.chdir("test/in/")
            sftp.chdir("prod/in/")
            # print(upload_filename)
            sftp.put(upload_filename, preserve_mtime=True)
            # close sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'ADIRONDACK UPLOAD failed'
        BODY = 'Unable to PUT .txt file to adirondack server.\n\n{0}'.format(
            str(e))
        sendmail(
            settings.ADIRONDACK_TO_EMAIL, settings.ADIRONDACK_FROM_EMAIL,
            BODY, SUBJECT
        )
        fn_write_error(BODY)


def main():

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
        # --------------------------
        # Create the txt file

        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(ADIRONDACK_QUERY)

        ret = list(data_result.fetchall())
        if ret is None:
            SUBJECT = '[adirondack Application] failed'
            BODY = "SQL Query returned no data."
            sendmail(
                settings.ADIRONDACK_TO_EMAIL, settings.ADIRONDACK_FROM_EMAIL,
                BODY, SUBJECT
            )
        else:
            fn_write_student_bio_header()
            # print("Query successful")
            with open(adirondackdata, 'a') as file_out:
                csvWriter = csv.writer(file_out, delimiter='|')
                encoded_rows = fn_encode_rows_to_utf8(ret)
                for row in encoded_rows:
                    csvWriter.writerow(row)
            file_out.close()

            # send file to SFTP Site..
            sftp_upload(adirondackdata)

    except Exception as e:
        fn_write_error("Error in adirondack buildcsv.py, Error = " + e.message)
        SUBJECT = '[adirondack Application] Error'
        BODY = "Error in adirondack student_bio.py, Error = " + e.message
        sendmail(settings.ADIRONDACK_TO_EMAIL, settings.ADIRONDACK_FROM_EMAIL,
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
