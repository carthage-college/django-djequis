# Added a few imports from primary_id.py on wilson..
import os
import sys
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy import text
# for testing comment out local settings file and point to another
# import settings
# import settings_purge_temp

import datetime
from time import strftime
import requests
import json
import string
import argparse
import shutil
from math import sin, cos, sqrt, atan2, radians

# import logging
# from logging.handlers import SMTPHandler
# from djtools.utils.logging import seperator

# django settings for script
import django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connections

from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from djtools.fields import TODAY

django.setup()

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")


# informix environment
# This matches code on Wilson for dup merge files
# Should NOT have to point to any other variables or constants
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH


# Probably only need the log directory
# CONSTANT_PMC_Log_Directory = '/opt/carthage/pmc/log'
# this is hard coded... but also in the settings file

############################################################
# From primary_id.py
############################################################
# # get the database connection
# def getDBConnection(db):
#     dbconn = getIFXEngine(db)
#     return dbconn
# # create the database engine
# def getIFXEngine(db):
#     engine = create_engine(
#         URL(
#             'informix',
#             username=settings.IFX_DB_USER,
#             password=settings.IFX_DB_PASS,
#             host=settings.IFX_DB_SERV,
#             port=settings.IFX_DB_PORT,
#             database=db
#         )
#     )
#     return engine
# # the constants above are in the wilson settings folder
############################################################

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Locate IDs marked for purge and update id_rec and cc_stage_merge to
    complete the process
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
        if database == 'cars':
            EARL = INFORMIX_EARL_PROD
        elif database == 'train':
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
        q_get_pool = '''SELECT cc_stage_merge_no, prim_id, sec_id, id1, id2, 
            fullname1, fullname2 
            FROM cc_stage_merge
            WHERE analysis_status not like '%PURGE%'
            AND adm_review = 'PURGE'
            AND  sec_id = 1360472
            ORDER BY fullname1
            '''


        sql_val = do_sql(q_get_pool, key=DEBUG, earl=EARL)

        # print(q_get_pool)
        if sql_val is not None:
            rows = sql_val.fetchall()

            for row in rows:
                purge_id = row[2]
                stage_merge_number = row[0]

                # ----------------------------------------------------
                # Verify that the sec_id is really the duplicate marked for
                #     purge
                # ----------------------------------------------------
                if (row[2] == row[4]) and (str(row[6])[:3] != 'DUP'):
                    fn_write_log("Sec ID " + str(row[4]) + ", " + str(row[6])
                                 + " not marked as DUP")
                elif (row[2] == row[3]) and (str(row[5])[:3] != 'DUP'):
                    fn_write_log("Sec ID " + str(row[3]) + ", " + str(row[5])
                                 + " not marked as DUP")
                else:

                    # ----------------------------------------------------
                    # Next go find the ID record
                    # ----------------------------------------------------
                    if purge_id is not None:
                        q_get_id_rec = "SELECT fullname, middlename, valid" \
                                    " FROM id_rec " \
                                     "WHERE id = " + str(purge_id)
                        # print(q_get_id_rec)
                        sql_val2 = do_sql(q_get_id_rec, key=DEBUG, earl=EARL)
                        row2 = sql_val2.fetchone()
                        # print("Row2 value = " + str(row2))
                        if row2 is not None:

                            # ------------------------------------------------
                            # Next update the ID record
                            # ------------------------------------------------
                            # print("Name = " + row2[0] + ", Valid = "
                            #  + row2[2] )
                            if str(row2[0]).find("PURGED") == -1:
                                q_upd_id_rec = '''UPDATE id_rec SET valid = ?,
                                    fullname = fullname[1, 24]||'(PURGED)'
                                    WHERE id = ?
                                                        '''
                                q_upd_id_rec_args = ('N', purge_id)
                                print(q_upd_id_rec + ", "
                                      + str(q_upd_id_rec_args))
                                engine.execute(q_upd_id_rec, q_upd_id_rec_args)

                                # --------------------------------------------
                                # Next update the stage merge record
                                # --------------------------------------------

                                q_upd_stage = '''UPDATE cc_stage_merge
                                    SET analysis_status = ?,
                                    final_actn_date = TODAY
                                    WHERE
                                    cc_stage_merge_no = ?
                                    and sec_id = ?
                                                       '''
                                q_upd_stage_args = ('PURGECOMPLETE',
                                        stage_merge_number, purge_id)
                                print(q_upd_stage + ", " +
                                      str(q_upd_stage_args))
                                engine.execute(q_upd_stage, q_upd_stage_args)

                                fn_write_log("ID " + str(purge_id) + ", " +
                                             row2[0] +  " Purged.")
                            else:
                                fn_write_log("Second ID " + str(purge_id)
                                    + ", " + row2[0] + " already purged")
                        else:
                            fn_write_error("Second ID " + str(purge_id) + ", "
                                           + " not in id_rec table")

                    else:
                        fn_write_error("Null value for secondary ID -"
                                       " no primary chosen")

    except Exception as e:
        # fn_write_error("Error in zip_distance.py for zip, Error = "
        #  + e.message)
        print("Error in purge_id.py: " + e.message)
        # finally:
        #     logging.shutdown()

def fn_write_log(msg):
    print(msg)
    # with open('purge_id.csv', 'w') as f:
    #     f.write(msg)

def fn_write_error(msg):
    # create error file handler and set level to error
    print("Error in purge_id.py: " + msg)
    # with open('purge_id.csv', 'w') as f:
    #     f.write(msg)



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
