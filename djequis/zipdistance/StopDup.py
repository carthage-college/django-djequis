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

# This code accesses the US Census Geocoding API to return geographical data
# for an address
# It returns Latitude, longitude, FIPS state and county codes

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

        # --------------------------------------------------------
        # Attempting to use the soundex (sounds like) field as part of the
        # matching search.
        # Idea would be to display possible matches and allow the user to
        # approve or reject
        # Soundex Calculator
        # Number	Represents the Letters
        # 1	        B, F, P, V
        # 2	        C, G, J, K, Q, S, X, Z
        # 3	        D, T
        # 4	        L
        # 5	        M, N
        # 6	        R
        # Soundex initially uses the consonants of a name to find a pattern
        # First character of code is first letter of name
        # Double letters like 'pp' are treated as one letter p, code 1
        # where two adjacent letters have the same code, the second is ignored
        # Names with prefixes - test both halves of the name separately
        # H and W have rules-when sandwiched between two consonants, ignore both
        # the h and the second consonant.  "Ashcroft" uses A,R,F,T and ignores the C
        # routine to parse out a name using these rules where
        # a soundex is not assigned would be tough to do and slow b/c would
        # have to parse every name in DB starting with first letter

        searchval_last = raw_input("Enter Last Name ")
        # searchval_last = x[:3]
        searchval_first = raw_input("Enter First Name ")
        # searchval_first = y[:4]
        searchval_zip = raw_input("Enter zip ")
        searchval_street = raw_input("Enter Street Address ")

        qval_sql = '''select distinct id, firstname, lastname, nvl(middlename,''),
             name_sndx, addr_line1, nvl(addr_line2,''), nvl(addr_line3,''), city, st, zip
            from id_rec where
            lastname like  "{0}%"       
            and firstname like "{1}%"   
            and addr_line1 like "{2}%"
			and zip like '{3}%'

        
        UNION
        select distinct 0 id, firstname, lastname, nvl(middlename,''),
             name_sndx, addr_line1, nvl(addr_line2,''), nvl(addr_line3,''), city, st, zip
            from lead_rec where
            lastname like  "{0}%"       
            and firstname like "{1}%"             
            and addr_line1 like "{2}%"
			and zip like '{3}%'
            
        UNION
        select distinct 0 id, firstname, lastname, nvl(middlename,''),
             name_sndx, addr_line1, nvl(addr_line2,''), nvl(addr_line3,''), city, st, zip
            from lead_rec where name_sndx in
                    (select distinct name_sndx from lead_rec
                    where lastname = "{4}" and name_sndx != '')
                    and firstname like "{1}%"
            and addr_line1 like "{2}%"
			and zip like '{3}%'
                    
            '''.format(searchval_last.capitalize()[:3],
                       searchval_first.capitalize()[:4],
                       searchval_street.capitalize()[:4],  searchval_zip,
                       searchval_last.capitalize())

        print(qval_sql)
        # Name_sndx in id rec is unreliable
        # Union  select distinct id, firstname, lastname, nvl(middlename, ''),
        # name_sndx, addr_line1, nvl(addr_line2, ''), nvl(addr_line3, ''), city, st, zip
        # from id_rec where name_sndx in (select distinct name_sndx from id_rec
        # where lastname like  "{0}%" and name_sndx != '') and firstname like "{1}%"

        sql_val = do_sql(qval_sql, key=DEBUG, earl=EARL)
        # ---------------------------------------------------------

        if sql_val is not None:
            rows = sql_val.fetchall()
            if rows is not None and rows != []:
                for row in rows:
                    id = str(row[0])
                    lname = str(row[2])
                    fname = str(row[1])
                    midname = str(row[3])
                    fullname =  lname + ', ' + fname + ' ' + midname
                    address = str(row[5]) + ' ' + str(row[6]) + ' ' + str(row[7])\
                              + " " +  str(row[8]) + ', ' + str(row[9])\
                              + ' ' + str(row[10])
                    print fullname + " - " + id + " - " +  address
                    # print row[0],  row[4],  row[10], row[11], row[12], row[13]
            else:
                print("No Match Found")
    except Exception as e:
        # fn_write_error("Error in zip_distance.py for zip, Error = " + e.message)
        print("Error in stopdupp.py - Error = " + str(e.message))
        # finally:
        #     logging.shutdown()


# def fn_single_address(v_street, v_city, v_state, v_zip):
#     try:
#         url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street=" \
#               + v_street + "&city=" + v_city + "&state=" + v_state + "&ZIP=" + v_zip + \
#               "&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
#
#         # Version with "layers=14" is bad!!!!  Does not return consitent format
#         # url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street=" \
#         #       + v_street + "&city=" + v_city + "&state=" + v_state + "&ZIP=" + v_zip + \
#         #       "&benchmark=Public_AR_Current&vintage=Current_Current&layers=14&format=json"
#
#         response = requests.get(url)
#         x = json.loads(response.content)
#         # rtn = x['result'][0]
#
#         if not x['result']['addressMatches']:
#             print("No match")
#         else:
#             # print("State from address components...")
#             address = x['result']['addressMatches'][0]['matchedAddress']
#             city = x['result']['addressMatches'][0]['addressComponents']['city']
#             state_abrv = x['result']['addressMatches'][0]['addressComponents']['state']
#             zip = x['result']['addressMatches'][0]['addressComponents']['zip']
#             streetName = x['result']['addressMatches'][0]['addressComponents']['streetName']
#             preQualifier = x['result']['addressMatches'][0]['addressComponents']['preQualifier']
#             preDirection = x['result']['addressMatches'][0]['addressComponents']['preDirection']
#             preType = x['result']['addressMatches'][0]['addressComponents']['preType']
#             suffixType = x['result']['addressMatches'][0]['addressComponents']['suffixType']
#             suffixDirection = x['result']['addressMatches'][0]['addressComponents']['suffixDirection']
#             suffixQualifier = x['result']['addressMatches'][0]['addressComponents']['suffixQualifier']
#
#             print(address)
#
#             y_coordinate = x['result']['addressMatches'][0]['coordinates']['y']
#             x_coordinate = x['result']['addressMatches'][0]['coordinates']['x']
#
#             # if not x['result']['addressMatches'][0]['geographies']['Unified School Districts']:
#             if not x['result']['addressMatches'][0]['geographies']['Counties']:
#                 print('No county detail data')
#             else:
#                 print('Found County Info')
#                 county_code = x['result']['addressMatches'][0]['geographies']['Counties'][0]['COUNTY']
#                 print("County Code = " + str(county_code))
#                 county_name = x['result']['addressMatches'][0]['geographies']['Counties'][0]['NAME']
#                 print("County = " + str(county_name))
#                 state_code = x['result']['addressMatches'][0]['geographies']['Counties'][0]['STATE']
#                 print("State FIPS = " + str(state_code))
#
#             if not x['result']['addressMatches'][0]['geographies']['States']:
#                 print('No state detail data')
#             else:
#                 print('Found State Info')
#                 state = x['result']['addressMatches'][0]['geographies']['States'][0]['NAME']
#                 print("State = " + str(state))
#
#             # print("Coordinates = " + str(x_coordinate) + ", " + str(y_coordinate))
#             # Calculate distance using latitude and longitude
#             # Note radians must be converted to a positive number
#             # Carthage latitude and longitude
#             radius_earth = 3958.756
#             lat1 = radians(42.62233)
#             lng1 = radians(abs(-87.828699))
#             lat2 = radians(float(y_coordinate))
#             lng2 = radians(abs(float(x_coordinate)))
#
#             dlon = lng2 - lng1
#             dlat = lat2 - lat1
#
#             a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#             c = 2 * atan2(sqrt(a), sqrt(1 - a))
#
#             distance = radius_earth * c
#             # print("Result rounded = " + "{:.0f}".format(distance))
#             dist = float("{:.2f}".format(distance))
#
#             print("Distance from Carthage = " + str(dist))
#
#     except Exception as e:
#         # fn_write_error("Error in zip_distance.py for zip, Error = " + e.message)
#         print("Error in address_lookup.py - Error = " + str(e.message))
#         # finally:
#         #     logging.shutdown()

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