import os
import string
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import datetime, timedelta
import codecs
import time
from time import strftime
import argparse
#import uuid
from sqlalchemy import text
import shutil
#import re
import logging
from logging.handlers import SMTPHandler

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
sys.path.append('/djequis/adp')

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

# from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djzbar.settings import INFORMIX_EARL_SANDBOX

from djtools.fields import TODAY

# Imports for additional modules and functions written as part of this project
from djequis.adp.utilities import fn_validate_field, fn_check_duplicates, \
    fn_write_log

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""
# write out the .sql file
scr = open("apdtocx_output.sql", "a")
# set start_time in order to see how long script takes to execute
start_time = time.time()

################################################
# Start of processing
################################################
def fn_process_cvid(carthid, adpid, ssn, adp_assoc_id, EARL):
    engine = get_engine(EARL)

    try:
        ##############################################################
        # Inserts or updates as needed into cvid_rec
        ##############################################################

        # Validate the cx_id
        v_cx_id = fn_validate_field(carthid, "cx_id", "cx_id", "cvid_rec",
                    "integer", EARL)
        #print("CX_ID = " + str(carthid))
        #print("v_CX_ID = " + str(v_cx_id))

        # Should also check for duplicates of the adp_id and associate_id
        # What to do in that case?
        v_adp_match = fn_check_duplicates(adpid, "adp_id", "cx_id", "cvid_rec",
                                 v_cx_id, "char", EARL)
        #print("Found_ID = " + str(v_adp_match))

        # By definition, associate ID cannot be a duplicate in ADP, but
        # possibility of duplicate might exist in CX
        v_assoc_match = fn_check_duplicates(adp_assoc_id, "adp_associate_id",
                       "cx_id", "cvid_rec", v_cx_id, "char", EARL)
        #print("Found ID = " + str(v_assoc_match))

        if v_cx_id == 0 and v_assoc_match == 0 and v_adp_match == 0:
            # Insert or update as needed to ID_rec
            q_insert_cvid_rec = '''
              INSERT INTO cvid_rec (old_id, old_id_num, adp_id, ssn, cx_id, 
              cx_id_char, adp_associate_id) 
              VALUES (?,?,?,?,?,?,?)'''
            args = (carthid, carthid, adpid, ssn, carthid, carthid, adp_assoc_id)
            # print(q_insert_cvid_rec)
            engine.execute(q_insert_cvid_rec, args)
            scr.write(q_insert_cvid_rec + '\n');
            fn_write_log("Inserted into cvid_rec table")
            # logger.info("Inserted into cvid_rec table");
        elif str(v_cx_id) != v_assoc_match and v_assoc_match != 0:
            print('Duplicate Associate ID found')
        elif str(v_cx_id) != str(v_adp_match) and v_adp_match != 0:
            print('Duplicate ADP ID found')
        else:
            q_update_cvid_rec = '''
              UPDATE cvid_rec 
              SET old_id = ?, old_id_num = ?, adp_id = ?, ssn = ?, 
              adp_associate_id = ? 
              WHERE cx_id = ?'''
            args = (carthid, carthid, adpid, ssn, adp_assoc_id, carthid)
            # print(q_update_cvid_rec)
            # fn_write_log("Update cvid_rec table")
            # logger.info("Update cvid_rec table");
            scr.write(q_update_cvid_rec + '\n');
            engine.execute(q_update_cvid_rec, args)

    except Exception as e:
        print(e)
    # finally:
    #     logging.shutdown()
