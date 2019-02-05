import os
import string
import sys
import csv
import datetime
import codecs
import argparse
from sqlalchemy import text
import shutil

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
            #python zip_distance.py - -database = train - -test
            EARL = INFORMIX_EARL_TEST
        elif database == 'sandbox':
            #python zip_distance.py - -database = sandbox - -test
            EARL = INFORMIX_EARL_SANDBOX
        else:
            # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None
        # establish database connection
        engine = get_engine(EARL)

        with open('fips_codes_abbr.csv', 'r') as f:
            d_reader = csv.DictReader(f, delimiter=',')

            for row in d_reader:
                print(str(row["State Abbreviation"]))
                print("State = " + row["State FIPS Code"])
                print("FIPS County = " + row["County FIPS Code"])
                print("Entity = " + row["GU Name"])
                print("Type = " + row["Entity Description"])
                st = row["State Abbreviation"].strip()
                city = row["GU Name"].strip()


                if row["Entity Description"] != 'County':
                    q_locate = '''
                               select * from zip_table 
                               where trim(st) = ? and trim(city) = ? 
                               '''
                    # and latitude is null and longitude is null
                    q_locate_args = (st, city)
                    print(q_locate)
                    print(str(q_locate_args))
                    engine.execute(q_locate, q_locate_args)

                else:
                    print("No Match")

    except Exception as e:
        # fn_write_error("Error in zip_distance.py for zip, Error = " + e.message)
        print("Error in fix_counties.py for zip, Error = " + str(e.message))
        # finally:
        #     logging.shutdown()

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

# Do update..
# for each zip code in USPS csv file...
#     q_upd_zip = '''
#         Update zip_table set latitude = ?, longitude = ?,
#         distance_to_carthage = ?
#         where zip = ?
#         '''
#     # and latitude is null and longitude is null
#     q_upd_zip_args = (float(lat), float(lng), dist, zp[:5])
#     # print(q_upd_zip)
#     print(str(q_upd_zip_args))
#     engine.execute(q_upd_zip, q_upd_zip_args)
# else:
#     print("No latitude or longitude for " + zp[:5])


# except Exception as e:
#     fn_write_error("Error in zip_distance.py for zip, Error = " + e.message)
#     print(e)
#     # finally:
#     #     logging.shutdown()

# def fn_write_error(msg):
#     # create error file handler and set level to error
#     with open('zip_code_error.csv', 'w') as f:
#         f.write(msg)

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
