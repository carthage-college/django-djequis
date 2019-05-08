import os
import sys
# import awscli
# import botocore
# import boto3
from botocore.exceptions import ClientError
import logging
import argparse

from handshake_sql import HANDSHAKE_QUERY

# set up command-line options
desc = """
    Utility to send Handshake files to Amazon Web Services bucket
"""


def fn_upload_aws_file(client, file_name, bucket_name,  object_name):
    try:
        print("In aws.py, " + file_name + ', ' + bucket_name + ', ' + object_name)
        print(awscli._awscli_data_path)
        # client = boto3.client('s3')
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
