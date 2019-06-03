#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import pyodbc
import time
from time import strftime
from datetime import datetime
import argparse
import shutil
import logging
from logging.handlers import SMTPHandler
# importing required modules
from zipfile import ZipFile
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
from picture_sql import PICTURE_ID_QUERY
from picture_sql import LENEL_PICTURE_QUERY

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


# def sftp_upload():
#     # by adding cnopts, I'm authorizing the program to ignore the host key and just continue
#     cnopts = pysftp.CnOpts()
#     cnopts.hostkeys = None # ignore known host key checking
#     # sFTP connection information for Adironcack
#     XTRNL_CONNECTION = {
#         'host':settings.ADIRONDACK_HOST,
#         'username':settings.ADIRONDACK_USER,
#         'password':settings.ADIRONDACK_PASS,
#         'port':settings.ADIRONDACKY_PORT,
#         'cnopts':cnopts
#     }
#     # set local path {/data2/www/data/adirondack/}
#     source_dir = ('{0}'.format(settings.ADIRONDACK_CSV_OUTPUT))
#     # get list of files and set local path and filenames
#     # variable == /data2/www/data/adirondack/{filename.csv}
#     directory = os.listdir(source_dir)
#     # sFTP PUT moves the COURSES.csv, USERS.csv, ENROLLMENT.csv files
#     # to the adirondack server
#     try:
#         with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
#             # change directory
#             sftp.chdir("upload/")
#             # loop through files in list
#             for listfile in directory:
#                 adirondackfiles = source_dir + listfile
#                 if adirondackfiles.endswith(".csv"):
#                     # sftp files if they end in .csv
#                     sftp.put(adirondackfiles, preserve_mtime=True)
#                 # delete original files from our server
#                 os.remove(adirondackfiles)
#             # close sftp connection
#             sftp.close()
#     except Exception, e:
#         SUBJECT = 'ADIRONDACK UPLOAD failed'
#         BODY = 'Unable to PUT .csv files to adirondack server.\n\n{0}'.format(str(e))
#         sendmail(
#             settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
#             BODY, SUBJECT
#         )

def get_all_file_paths(directory):
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

            # returning all file paths
    return file_paths


def main():

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python buildcsv.py --database=train --test
    # production server (psm), you would execute:
    # ==> python buildcsv.py --database=cars
    # without the --test argument
    ##########################################################################

    # set date and time to be added to the filename
    datestr = datetime.now().strftime("%Y%m%d")
    # print(datestr)

    # set date and time to be added to the archive filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # print(datetimestr)

    # Defines file names and directory location
    adirondackdata = ('{0}carthage_students.txt'.format(
         settings.ADIRONDACK_CSV_OUTPUT))

    # set archive directory
    archived_destination = ('{0}carthage_users-{1}.txt'.format(
        settings.ADIRONDACK_CSV_ARCHIVED, datetimestr
        ))

    try:
        print("try")
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

        #         # Query CX and start loop through records
        #
        # print(PICTURE_ID_QUERY)
        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(PICTURE_ID_QUERY)

        ret = list(data_result.fetchall())
        if ret is None:
            SUBJECT = '[adirondack Application] failed'
            BODY = "SQL Query returned no data."
            print(SUBJECT)

            # sendmail(
            #     settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
            #     BODY, SUBJECT
            # )
        else:
            print("Query successful")
            try:
                connection = pyodbc.connect(MSSQL_LENEL_EARL)
                for row in ret:
                    # print(row[0] + '.jpg')
                    LENEL_PICTURE_ARG = row[0]

                    print(LENEL_PICTURE_QUERY)
                    print(LENEL_PICTURE_ARG)

                    result = connection.execute(LENEL_PICTURE_QUERY, LENEL_PICTURE_ARG)

                    for row in result:
                        print(row)

                    result.close()

                connection.close()
            except Exception as e:
                print("Error getting photo " + e.message)

            # ###############################################
            # # Write all files to a single zip
            # # path to folder which needs to be zipped
            # directory = './python_files'
            #
            # # calling function to get all file paths in the directory
            # file_paths = get_all_file_paths(directory)
            #
            # # printing the list of all files to be zipped
            # # print('Following files will be zipped:')
            # for file_name in file_paths:
            #     print(file_name)
            #
            #     # writing files to a zipfile
            # with ZipFile('my_python_files.zip', 'w') as zip:
            #     # writing each file one by one
            #     for file in file_paths:
            #         zip.write(file)
            #
            # print('All files zipped successfully!')


            # # ================================================
            # # READING A ZIP FILE
            # # specifying the zip file name
            # file_name = "carthage_studentphotos.zip"
            #
            # # opening the zip file in READ mode
            # with ZipFile(file_name, 'r') as zip:
            # # printing all the contents of the zip file
            # zip.printdir()
            #
            # # extracting all the files
            # print('Extracting all the files now...')
            # zip.extractall()
            # print('Done!')

            # send file to SFTP Site..


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
