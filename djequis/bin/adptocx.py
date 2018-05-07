import os
import sys
import pysftp
import csv
import datetime
from datetime import date
import time
from time import strftime
import argparse
import uuid
from sqlalchemy import text
import shutil
import re
import logging
from logging.handlers import SMTPHandler
import adpftp

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from djequis.core.utils import sendmail

from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""
parser = argparse.ArgumentParser(description=desc)

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


adpftp.file_download()


# sFTP fetch (GET) downloads the file from ADP file from server
# def file_download():
#     cnopts = pysftp.CnOpts()
#     cnopts.hostkeys = None
#     # External connection information for ADP Application server
#     XTRNL_CONNECTION = {
#        'host':settings.ADP_HOST,
#        'username':settings.ADP_USER,
#        'password':settings.ADP_PASS,
#        'cnopts':cnopts
#     }
#
#     ############################################################################
#     # sFTP GET downloads the CSV file from ADP server and saves in local directory.
#     ############################################################################
#     with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
#         sftp.chdir("adp/")
#         # Remote Path is the ADP server and once logged in we fetch directory listing
#         remotepath = sftp.listdir()
#         # Loop through remote path directory list
#         for filename in remotepath:
#             remotefile = filename
#             # set local directory for which the ADP file will be downloaded to
#             local_dir = ('{0}'.format(
#                 settings.ADP_CSV_OUTPUT
#             ))
#             localpath = local_dir + remotefile
#             # GET file from sFTP server and download it to localpath
#             sftp.get(remotefile, localpath)
#             #############################################################
#             # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
#             # from sFTP (ADP) server
#             #############################################################
#             #sftp.remove(filename)
#     sftp.close()
#
# file_download()
