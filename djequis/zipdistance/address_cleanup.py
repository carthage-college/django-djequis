import os
import requests
import sys
import csv
import argparse
import string
import json
import time
from datetime import datetime, timedelta
from math import sin, cos, sqrt, atan2, radians


from django.conf import settings
from django.core.urlresolvers import reverse
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

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

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


def update_id(addr1, addr2,  addr3, city, state, zp, id, engine):
    # Theoretically, since we are beginning with a select from id_rec
    # we should never need an insert statement
    idrec_sql = "UPDATE id_rec SET addr_line1 = ?, addr_line2 = ?, " \
                "addr_line3 = ?, city = ?, st = ?, zip = ?, " \
                "cass_cert_date = TODAY " \
                "WHERE id = ?"
    idrec_args = (addr1, addr2,  addr3, city, state, zp,  id)
    # print(idrec_sql, idrec_args)
    # print(engine)
    # engine.execute(idrec_sql, idrec_args)



def update_profile(state,  city, id, engine):
    # this will add the proper county and state codes
    # Every id record should have a corresponding profile record, so no
    # insert needed.
    profile_sql = "UPDATE profile_rec SET res_st = ?, res_cty = ? " \
                  "WHERE id = ?"
    # profile_args = (str(row[15]), str(row[16]), row[0])
    profile_args = (state, city, id)
    # print(profile_sql, profile_args)
    # engine.execute(profile_sql, profile_args)


def fn_fix_unit(addr):
    exclude = ["SUITE", "BLDG", "LOT", "UNIT", "APT", "STE", "#"]

    # Break up your address into its parts
    chopped = addr.split(" ")

    # Placeholder for final string
    l_addr = ""
    unit = ""
    if addr.find('#') > -1:
        x = addr.find('#')
        l_addr = addr[:x]
        unit = addr[x:]
    else:
        # Grab your address components
        for piece in chopped:
            # Check if they are in the exclusion list
            # If not, add to your output.
            if piece.upper().translate(None, string.punctuation) \
                    not in exclude:
                l_addr = addr
            # If you hit a unit number, break the loop
            # Note this works only for suffix lot types
            else:
                pos = addr.find(piece)
                l_addr = addr[:pos]
                unit = addr[pos:]
                break

    return l_addr, unit

# This code accesses the US Census Bureau API to get geographic data by address
# It takes a csv file as a batch upload and returns a csv file with the data
# Return includes Latitude, longitude, FIPS state and county codes

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

        #  -------------------------------------------------------
        # 1. Query the database
        # 10,000 record batch is the maximum.   It would return typically in
        # around 20 minutes.  First test, 24:36
        #  -------------------------------------------------------
        # Use the cass_cert_date to mark records that have been validated
        qval_sql = '''select id_rec.id, 
                trim(id_rec.addr_line1)||' '||trim(nvl(id_rec.addr_line2,
        		''))||' '||trim(nvl(id_rec.addr_line3,'')) street, 
        		id_rec.city, id_rec.st, id_rec.zip
                from id_rec where cass_cert_date is null
                AND length(addr_line1) > 0 
                limit 10'''
        # print(qval_sql)
        # NOTE:  Max batch is 10,000 records
        sql_val = do_sql(qval_sql, key=DEBUG, earl=EARL)

        #  -------------------------------------------------------
        # 2. write results to a csv
        #  -------------------------------------------------------

        if sql_val is not None:
            rows = sql_val.fetchall()
            with open('CXAddresses.csv', 'w') as CXOutput:
                csvWriter = csv.writer(CXOutput)

                for row in rows:
                    # print(row)
                    v_id = row[0]
                    x = row[1]
                    rslt = fn_fix_unit(row[1])
                    v_street = rslt[0]
                    v_unit = rslt[1]
                    v_city = row[2]
                    v_state = row[3]
                    v_zip = row[4]
                    # csvWriter.writerow(v_id, v_fullmane, v_street, v_city,
                    # v_state, v_zip)
                    # print('CX Address = ' + str(v_id) + ", " + v_street
                    # + ", " + v_unit + ", " + v_city + ', ' + v_state
                    # + ', ' + v_zip)
                    csvWriter.writerow(row)
            CXOutput.close()
        #  -------------------------------------------------------
        # 3. Send the csv to Geocode
        #  -------------------------------------------------------
        sendtime = datetime.now()
        print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))
        url = 'https://geocoding.geo.census.gov/geocoder/geographies/addressbatch?form'
        payload = {'benchmark': 'Public_AR_Current',
                   'vintage': 'Current_Current'}
        files = {'addressFile': ('CXAddresses.csv', open('CXAddresses.csv',
                                                         'rb'), 'text/csv')}
        r = requests.post(url, files=files, data=payload)

        results = str(r.text)
        results = results.replace('"', '')
        results = results.split('\n')
        print("Time of return = " + time.strftime("%Y%m%d%H%M%S"))
        returntime = datetime.now()
        diff = returntime - sendtime
        print("Elapsed time: " + str(diff))

        # print(results)

        #  -------------------------------------------------------
        # 4. Write the results to second csv
        #  -------------------------------------------------------
        with open('geocodeOutput.csv', 'w') as geocodeOutput:
            w = csv.writer(geocodeOutput, delimiter=',', quotechar='"',
                           quoting=csv.QUOTE_MINIMAL)
            w.writerows([c.strip() for c in r.split(',')] for r in results)
        geocodeOutput.close()

        #  -------------------------------------------------------
        # 5. Read the new csv
        #  -------------------------------------------------------
        with open('geocodeOutput.csv', 'r') as data:
            read_csv = csv.reader(data, delimiter=',')
            for row_count, row in enumerate(read_csv):
                # print("\n" + "Row count = " + str(row_count + 1))
                # print("ID = " + row[0])
                if row[0] == '':
                    original_address = ''
                    # could essentially do nothing
                    # print("NO Record at row " + str(row_count + 1))
                if str(row).find('--BadAddr--') > 0:
                    original_address = str(row)
                    raise ValueError("Bad Address: " + original_address)
                    # could essentially do nothing
                    # print("NO Record at row " + str(row_count + 1))
                elif row[5] == 'No_Match':
                    # print("Match = " + row[5])
                    original_address = row[1] + ", " + row[2] + ", " + row[
                         3] + ", " + row[4]
                    # print("Original Address = " + original_address)
                    # print("FIPS State and Zip Undetermined")

                elif row[6] == "Non_Exact":
                    # print("Match = " + row[5] + " " + row[6])
                    original_address = row[1] + ", " + row[2] + ", " + row[
                        3] + ", " + row[4]
                    # print("Original Address = " + original_address)
                    correct_address = row[7] + ", " + row[8] + ", " + row[
                        9] + ", " + row[10]
                    # print("Partial Match = " + correct_address)
                    # coordinates = str(row[12] + ", " + str(row[11]))
                    # print("Latitude and Longitude = " + str(coordinates))
                    FIPS = str(row[15]) + "-" + str(row[16])
                    # print("FIPS State and Zip = " + FIPS)
                    # print("Distance from Carthage = " + str(
                    #     fn_calc_distance(row[11], row[12])))

                    # update_id(str(row[7]), '', '', str(row[8]), str(row[9]),
                    #           str(row[10]), str(row[0]), engine)
                    #
                    # update_profile(str(row[15]), str(row[16]), row[0], engine)

                else:
                    # print("Match = " + row[5] + " " + row[6])
                    original_address = row[1] + ", " + row[2] + ", " + row[
                        3] + ", " + row[4]
                    # print(original_address)
                    correct_address = row[7] + ", " + row[8] + ", " + row[
                        9] + ", " + row[10]
                    # print(correct_address)
                    # coordinates = str(row[12] + ", " + str(row[11]))
                    # print("Latitude and Longitude = " + str(coordinates))
                    FIPS = str(row[15]) + "-" + str(row[16])
                    # print("FIPS State and Zip = " + FIPS)
                    # print("Distance from Carthage = " + str(
                    #     fn_calc_distance(row[11], row[12])))

                    #  -------------------------------------------------------
                    # 6. Update CX as needed
                    #  -------------------------------------------------------
                    # update_id(str(row[7]), '', '', str(row[8]), str(row[9]),
                    #           str(row[10]), str(row[0]), engine)
                    #
                    # update_profile(str(row[15]), str(row[16]), row[0], engine)


        # Question remains as to what else we will update
        # Will we correct address in ID rec?
        # Do we care about addresses in AA rec for this purpose?

    except ValueError as e:
        print(e.args)
        pass
    except Exception as e:
        print("Error = " + e.message)
        # finally:
        #     logging.shutdown()

def fn_calc_distance(x,y):
    # Calculate distance using latitude and longitude
    # Note radians must be converted to a positive number
    # Carthage latitude and longitude
    radius_earth = 3958.756
    lat1 = radians(42.62233)
    lng1 = radians(abs(-87.828699))
    lat2 = radians(float(y))
    lng2 = radians(abs(float(x)))

    dlon = lng2 - lng1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = radius_earth * c
    # print("Result rounded = " + "{:.0f}".format(distance))
    dist = float("{:.2f}".format(distance))

    return (dist)

def fn_write_error(msg):
    # create error file handler and set level to error
    with open('zip_code_error.csv', 'w') as f:
        f.write(msg)


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
