import os
import requests
import json
import string
import sys
import csv
import datetime
import codecs
import argparse
from sqlalchemy import text
import shutil
from math import sin, cos, sqrt, atan2, radians

# import logging
# from logging.handlers import SMTPHandler
# from djtools.utils.logging import seperator

from django.conf import settings
from django.core.urlresolvers import reverse
# import requests
# import json
from math import sin, cos, sqrt, atan2, radians

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')

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
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Update Zip table with Latitude, Longitude, Distance from Carthage
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


def main():
    try:
        # set global variable
        global EARL
        # determines which database is being called from the command line
        # if database == 'cars':
        #     EARL = INFORMIX_EARL_PROD
        if database == 'train':
            #python address_lookup.py --database=train --test
            EARL = INFORMIX_EARL_TEST
        elif database == 'sandbox':
            #python address_lookup.py --database=sandbox --test
            EARL = INFORMIX_EARL_SANDBOX
        else:
            # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)

        #----------------------------------------------------
        # First go find the records marked for purging
        #----------------------------------------------------
        q_get_pool = '''select cc_stage_merge_no, prim_id, sec_id, id1, id2, 
            fullname1, fullname2 from cc_stage_merge
            where analysis_status not like '%PURGE%'
            and adm_review = 'PURGE'  '''
        sql_val = do_sql(q_get_pool, key=DEBUG, earl=EARL)

        if sql_val is not None:
            rows = sql_val.fetchall()

            # Need to add some logic here to verify that the sec_id is
            # really the duplicate marked for merge

            for row in rows:
                # print(row[0])
                purge_id = row[2]
                stage_merge_number = row[0]

                # ----------------------------------------------------
                # Next go find the ID record
                # ----------------------------------------------------
                if purge_id is not None:
                    q_get_id_rec = "select fullname, middlename, valid from id_rec " \
                                 "where id = " + str(purge_id)
                    # print(q_get_id_rec)
                    sql_val2 = do_sql(q_get_id_rec, key=DEBUG, earl=EARL)

                    if sql_val2 is not None:

                        # ----------------------------------------------------
                        # Next update the ID record
                        # ----------------------------------------------------

                        row2 = sql_val2.fetchone()
                        # for row2 in rows2:
                        print("Name = " + row2[0] + ", Valid = " + row2[2] )

                        q_upd_id_rec = '''update id_rec set valid = ?,
                            fullname = fullname[1, 24] | | '(PURGED)'
                            where id = ?
                                                '''

                        q_upd_id_rec_args = ('N', purge_id)
                        # print(q_upd_id_rec)
                        # print(str(q_upd_id_rec_args))
                        # engine.execute(q_upd_id_rec, q_upd_id_rec_args)

                        # ----------------------------------------------------
                        # Next update the stage merge record
                        # ----------------------------------------------------

                        q_upd_stage = '''UPDATE cc_stage_merge 
                            SET analysis_status = ?,
                            final_actn_date = TODAY
                            WHERE
                            cc_stage_merge_no = ?
                            and sec_id = ?
                                                '''

                        q_upd_stage_args = ('PURGECOMPLETE', stage_merge_number,
                                             purge_id)
                        print(q_upd_stage)
                        print(str(q_upd_stage_args))
                        # engine.execute(q_upd_stage, q_upd_stage_args)




    except Exception as e:
        # fn_write_error("Error in zip_distance.py for zip, Error = " + e.message)
        print(e.message)
        # finally:
        #     logging.shutdown()

def fn_write_error(msg):
    # create error file handler and set level to error
    with open('zip_code_error.csv', 'w') as f:
        f.write(msg)

    # handler = logging.FileHandler(
    #     '{0}zip_distance_error.log'.format(settings.LOG_FILEPATH))
    # handler.setLevel(logging.ERROR)
    # formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
    #                               datefmt='%m/%d/%Y %I:%M:%S %p')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)
    # logger.error(msg)
    # handler.close()
    # logger.removeHandler(handler)
    # fn_clear_logger()
    # return("Error logged")


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

    if database != 'cars' and database != 'train' and database != \
            'sandbox':
        print "database must be: 'cars' or 'train' or 'sandbox'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())