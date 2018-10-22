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

# There are two possible methods for dealing with updating the county codes
# One is a record at a time
# The other is by batch, 1000 records maximum, using a csv file
# The latter would need to loop through the records, write to the csv file
# in the format "Unique ID, Street address, City, State, ZIP"
# It would also need to count and if the number of records exceeds 1000,
# create a second csv file
# The latter, batch method, may not return all the fields we need.
# It does include Latitude, longitude, FIPS state and county codes

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


        #-------------------------------------------------------
        # Read in records first.
        #-------------------------------------------------------
        # searchval = "Winthrop Harbor"
        #
        # qval_sql = "select id, fullname, addr_line1, addr_line2, addr_line3, " \
        #            "city, st, zip from id_rec where city = '" \
        #            + str(searchval) + "'"
        #
        # sql_val = do_sql(qval_sql, key=DEBUG, earl=EARL)
        #
        # if sql_val is not None:
        #     rows = sql_val.fetchall()
        #
        #     for row in rows:
        #         # response2 = requests.get("http://www.zipcodeapi.com/rest/" + APIKey + "/"
        #         # + distformat + "/" + CarthZip + "/" + zipcode + "/" + distunits)
        #         v_street = row[2]
        #         v_city = row[5]
        #         v_state = row[6]
        #         v_zip = row[7]

        # Write the query results to a csv file that can be uploaded as batch
        # The first item is unique id, so we need to use the Carthage ID
        # so that we will have it on the return...






        # This seems to be the correct method, but it just returns a massive xml page
        url = 'https://geocoding.geo.census.gov/geocoder/geographies/addressbatch?form'
        payload = {'benchmark': 'Public_AR_Current',
                   'vintage': 'Current_Current'}
        files = {'addressFile': ('Addresses.csv', open('Addresses.csv', 'rb'), 'text/csv')}
        r = requests.post(url, files=files, data=payload)
        # just a 404 error
        print r.status_code
        results = str(r.text)
        results = results.replace('"', '')
        results = results.split('\n')
        print(results)
        with open('geocodeOutput.csv', 'w') as geocodeOutput:
            w = csv.writer(geocodeOutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            w.writerows([c.strip() for c in r.split(',')] for r in results)

        with open('geocodeOutput.csv', 'r') as data:
            read_csv = csv.reader(data, delimiter=',')
            for row in read_csv:
                print("ID = " + row[0])
                print("Street = " + row[1])
                print("City = " + row[2])
                print("State = " + row[3])
                print("Zip = " + row[4])
                print("Match = " + row[5])
                print("Match Type = " + row[6])
                print("Corrected Street = " + row[7])
                print("Corrected City = " + row[8])
                print("Corrected State = " + row[9])
                print("Zip = " + row[10])
                print("Longitude = " + row[11])
                print("Latitude = " + row[12])
                print("Side = " + row[13])
                print("FIPS State = " + row[14])
                print("FIPS County = " + row[15])

                # Return file is also a csv, so no JSON
                # Loop through csv, update tables as needed

                y_coordinate = row[12]
                x_coordinate = row[11]

                # print("Coordinates = " + str(x_coordinate) + ", " + str(y_coordinate))

                # Calculate distance using latitude and longitude
                # Note radians must be converted to a positive number
                # Carthage latitude and longitude
                radius_earth = 3958.756
                lat1 = radians(42.62233)
                lng1 = radians(abs(-87.828699))
                lat2 = radians(float(y_coordinate))
                lng2 = radians(abs(float(x_coordinate)))

                dlon = lng2 - lng1
                dlat = lat2 - lat1

                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))

                distance = radius_earth * c
                # print("Result rounded = " + "{:.0f}".format(distance))
                dist = float("{:.2f}".format(distance))

                print("Distance from Carthage = " + str(dist))


                # Finally, update the particular CX tables
                # Update profile rec set ...
                # This creates a new problem in that the return file is no
                # longer associated to a person's ID number
                # How then do we make the match?




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