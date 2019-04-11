import os
import sys
import awscli
import botocore
import boto3
from datetime import datetime
import time
from time import strftime

from botocore.exceptions import ClientError
import logging
from logging.handlers import SMTPHandler

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Utility to send Handshake files to Amazon Web Services bucket
"""

# Test with this then remove, use the standard logging mechanism
logger = logging.getLogger(__name__)

def main():
    # Defines file names and directory location
    handshakedata = ('{0}users.csv'.format(settings.HANDSHAKE_CSV_OUTPUT))
    print("Handshakedata = " + handshakedata)

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



def fn_upload_file(file_name, bucket_name,  object_name):
    try:
        print("In aws.py, " + file_name + ', ' + bucket_name + ', ' + object_name)

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
        print("Error in fn_upload_file = " + e.message)
    return True

if __name__ == '__main__':
    main()