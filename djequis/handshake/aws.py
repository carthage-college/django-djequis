import os
import sys
import csv
import awscli
import botocore
import boto3
import requests

from botocore.exceptions import ClientError
from datetime import datetime
import time
from time import strftime
import argparse
import logging
from logging.handlers import SMTPHandler

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from djequis.core.utils import sendmail
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

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
    """Exercise upload_file()"""

    # Defines file names and directory location
    # object_name = 'OBJECT_NAME'  #If not specified then same as file_name
    datestr = datetime.now().strftime("%Y%m%d")
    object_name = (datestr + '_users.csv')
    file_path = settings.HANDSHAKE_CSV_OUTPUT
    file_name = file_path + object_name
    # According to this https://github.com/timkay/aws/wiki/S3-Prefixes-and-Delimiters-Explained
    # The bucket is the entire path name
    # The key is the full file name that comes after the bucket
    # A prefix is just a filter, which we won't need
    # The file on Amazon that we are placing is called a Key, and is the whole
    # path after the bucket
    bucket_name = settings.HANDSHAKE_BUCKET  # bucket_name = 'importer-production-carthage'
    remote_folder =  settings.HANDSHAKE_S3_FOLDER  # importer-production-carthage/
    key_name = remote_folder + '/' + object_name

    # print("File Path = " + file_path)
    print("Local File Name and Path = " + file_name)
    print("Local Object Name = " + object_name)
    print("Bucket = " + bucket_name)
    print("Remote Folder = " + remote_folder)
    print("Remote Key/Object Name =" + key_name)

    print("Upload File = " + file_name + ', ' + bucket_name + ', ' + key_name)
    upload_file(file_name, bucket_name, key_name)

    if os.path.isfile(file_name):
        print("File Name = " + file_name)
        # We want to pass the local file name and directory, the AWS Bucket name
        #  and the object or key that will name the file on Handshake's location
        upload_file(file_name, bucket_name, key_name)
        print("Upload File = " + file_name + ', '+ bucket_name + ', ' + key_name)
    #     upload_file(file_name, bucket_name,  object_name)
    # else:
    #     print("No File")



    # # Set up logging
    # logging.basicConfig(level=logging.DEBUG,
    #                     format='%(levelname)s: %(asctime)s: %(message)s')
    #
    # # Upload a file
    # response = upload_file(file_name, bucket_name, object_name)
    # if response:
    #     logging.info('File was uploaded')

def upload_file(file_name, bucket_name,  object_name):
    try:

        #-------------------------------------------------
        #This works up to a point, so don't lose it
        # session = boto3.Session()
        # print("Session = " + str(session))  # returns Session(region_name='us-east-1')
        # credentials = session.get_credentials()
        # secret = credentials.secret_key  #returns the secret
        # print('Secret =' + secret)
        #SO ALL THIS WORKS... what next?
        # res = session.get_available_resources()
        # print('Resourses =' + str(res))
        # This returns a list of resources including "s3"
        # client = session.client('s3')
        # print("Client = " + str(client))

        #-------------------------------------------------
        #  NOTE: Can't return anything from Handshake because there is no read access to the bucket

        client = boto3.client('s3')
        # print("Client = " + str(client))     #returns <botocore.client.S3 object at 0x7fe83f038d90>
        # THIS WORKS DO NOT LOSE!
        # client.upload_file(Filename='20190404_users.csv',
        #                      Bucket='handshake-importer-uploads',
        #                      Key='importer-production-carthage/20190404_users.csv')

        print(file_name,bucket_name,object_name)
        # REPLACE WITH
        # client.upload_file(Filename=file_name, Bucket=bucket_name, Key=object_name)


    except ClientError as e:
        # logging.error(e)
        print(e)
        return False
    return True

if __name__ == '__main__':
    main()