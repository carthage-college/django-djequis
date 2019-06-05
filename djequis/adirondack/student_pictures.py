#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import pysftp
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

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)


def sftp_upload(upload_file):
    print("In File Upload")
    print(upload_file)
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

    # set local path {/data2/www/data/adirondack/}
    source_dir = ('{0}'.format(settings.ADIRONDACK_JPG_OUTPUT))
    # get list of files and set local path and filenames
    # variable == /data2/www/data/adirondack/{filename.zip}
    directory = os.listdir(source_dir)

    try:
        print("Make Connection")
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            # change directory
            print("Change Directory at SFTP Site")
            # sftp.chdir("prod/in/studentphotos/")
            sftp.chdir("test/in/")
            sftp.put(upload_file, preserve_mtime=True)
            # delete original files from our server
            # os.remove(adirondackfiles)
            # close sftp connection
            sftp.close()
    except Exception, e:
        SUBJECT = 'ADIRONDACK UPLOAD failed'
        BODY = 'Unable to PUT .zip file to adirondack server.\n\n{0}'.format(str(e))
        # sendmail(
        #     settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
        #     BODY, SUBJECT
        # )
        print(BODY)


def main():

    ##########################################################################
    # development server (bng), you would execute:
    # ==> python student_pictures.py --database=train --test
    # production server (psm), you would execute:
    # ==> python student_pictures.py --database=cars
    # without the --test argument
    ##########################################################################

    # set date and time to be added to the filename
    datestr = datetime.now().strftime("%Y%m%d")
    # print(datestr)

    # set date and time to be added to the archive filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # print(datetimestr)

    filepath = settings.ADIRONDACK_JPG_OUTPUT

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

        # print(PICTURE_ID_QUERY)
        engine = get_engine(EARL)  # do_sql calls get engine
        data_result = engine.execute(PICTURE_ID_QUERY)

        retID = list(data_result.fetchall())
        if retID is None:
            SUBJECT = '[adirondack Application] failed'
            BODY = "SQL Query returned no data."
            print(SUBJECT)
            # sendmail(
            #     settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
            #     BODY, SUBJECT
            # )
        else:
            print("Query 1 successful")
            try:

                for row in retID:
                    LENEL_PICTURE_ARG = row[0]
                    # print("Query = " + LENEL_PICTURE_QUERY)
                    # print("ARG = " + LENEL_PICTURE_ARG)
                    try:
                        # query blob data form the authors table
                        conn = pyodbc.connect(MSSQL_LENEL_EARL)
                        result = conn.execute(LENEL_PICTURE_QUERY.format(LENEL_PICTURE_ARG))

                        for row1 in result:
                            photo = row1[0]
                            filename = str(LENEL_PICTURE_ARG) + ".jpg"
                            # write blob data into a file
                            write_file(photo, filepath + "/" + filename)
                        result.close()

                    except ValueError:
                        print("Value Error getting photo")
                    except TypeError:
                        print("Type Error getting photo")
                    except Exception as e:
                        if e.__class__ == 'pyodbc.DataError':
                            pass
                    finally:
                        conn.close()

            except Exception as e:
                print("Error getting photo " + e.message)

            if os.path.exists(filepath + "carthage_studentphotos.zip"):
               os.remove(filepath + "carthage_studentphotos.zip")
            # print(filepath)

            shutil.make_archive("carthage_studentphotos", 'zip', filepath)
            shutil.move("carthage_studentphotos.zip", filepath)

            # send file to SFTP Site..
            sftp_upload(filepath + "carthage_studentphotos.zip")

    except Exception as e:

        # fn_write_error("Error in adirondack buildcsv.py, Error = " + e.message)
        SUBJECT = '[adirondack Application] Error'
        BODY = "Error in adirondack buildcsv.py, Error = " + e.message
        # sendmail(settings.ADIRONDACK_TO_EMAIL,settings.ADIRONDACK_FROM_EMAIL,
        #     BODY, SUBJECT)
        print(SUBJECT, BODY)


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
