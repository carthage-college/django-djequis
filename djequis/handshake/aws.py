import os
import sys
import awscli
import botocore
import boto3
from datetime import datetime
import time
import logging
import argparse

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings

from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine, get_session
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from handshake_sql import HANDSHAKE_QUERY

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Utility to send Handshake files to Amazon Web Services bucket
"""
# Test with this then remove, use the standard logging mechanism
logger = logging.getLogger(__name__)

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


def fn_upload_file(file_name, bucket_name,  object_name):
    try:
        print("In aws.py, " + file_name + ', ' + bucket_name + ', ' + object_name)
        print(awscli._awscli_data_path)
        client = boto3.client('s3')
        print("Client = " + str(client))     #returns <botocore.client.S3 object at 0x7fe83f038d90>
        # THIS WORKS DO NOT LOSE!
        print("Upload will use: " + file_name + ", " + bucket_name + ", " + object_name )
        # client.upload_file(Filename='20190404_users.csv',
        #                      Bucket='handshake-importer-uploads',
        #                      Key='importer-production-carthage/20190404_users.csv')

        # REPLACE WITH
        # client.upload_file(Filename=file_name, Bucket=bucket_name, Key=object_name)

    except boto3.exceptions.S3UploadFailedError as e:
        # logging.error(e)
        print(e)
        return "Error = s3UploadFailedError in aws.py " + e.message
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # logging.error(e)
            print("The object does not exist.")
            return "Error = Client Error in aws.py " + e.message
        else:
            raise
            return "Unknown error in aws.py " + e.message
    except Exception as e:
        print("Error in fn_upload_file = " + e.message + e.__str__())
    return True

def main():
    # Defines file names and directory location
    handshakedata = ('{0}users.csv'.format(settings.HANDSHAKE_CSV_OUTPUT))
    print("Handshakedata = " + handshakedata)

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

        #______****************************************
        # WHEN I MAKE THE DATABASE CALL, IT MESSES UP THE BOTO3 CLIENT CALL??
        # data_result = do_sql(HANDSHAKE_QUERY, key=DEBUG, earl=EARL)
        #______****************************************

        # ret = list(data_result.fetchall())
        # if ret is None:
        #     print("Data missing")
        # #     # fn_write_log("Data missing )
        # else:
        #     print("Data found")
        #     # with open(handshakedata, 'a') as file_out:
        #     #     csvWriter = csv.writer(file_out)
        #     #     for row in ret:
        #     #          csvWriter.writerow(row)
        #     # file_out.close()
        # data_result = None

        object_name = ('users.csv')
        bucket_name = settings.HANDSHAKE_BUCKET
        remote_folder = settings.HANDSHAKE_S3_FOLDER
        key_name = remote_folder + '/' + object_name

        file_date = time.strftime('%m/%d/%Y',
                                  time.gmtime(os.path.getmtime(handshakedata)))
        print("Date of file = " + file_date)

        print("Local File Name and Path = " + handshakedata)
        # print("Local Object Name = " + object_name)
        print("Bucket = " + bucket_name)
        print("Remote Folder = " + remote_folder)
        print("Remote Key/Object Name =" + key_name)
        print("Upload File = " + handshakedata + ', ' + bucket_name + ', ' + key_name)
        time.sleep(3)
        try:
            ret = fn_upload_file('/data2/www/data/handshake/users.csv', bucket_name, key_name)
            print(ret)
        except Exception as e:
            print("Upload error = " + e.message + ', ' + str(e.args))

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
