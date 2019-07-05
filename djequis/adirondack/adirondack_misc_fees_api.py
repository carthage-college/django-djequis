import os
import sys
import calendar
import time
import datetime
import codecs
# import argparse
import hashlib
import json
import requests
import csv
import logging
from logging.handlers import SMTPHandler


# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings
from django.db import connections
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from adirondack_sql import ADIRONDACK_QUERY
from adirondack_utilities import fn_write_error, fn_write_misc_header

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

# normally set as 'debug" in SETTINGS
DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Collect adirondack data ASCII Post
"""
# parser = argparse.ArgumentParser(description=desc)

# Test with this then remove, use the standard logging mechanism
logger = logging.getLogger(__name__)

# parser.add_argument(
#     "--test",
#     action='store_true',
#     help="Dry run?",
#     dest="test"
# )
# parser.add_argument(
#     "-d", "--database",
#     help="database name.",
#     dest="database"
# )





def main():
    try:
      # Time in GMT
      # GMT Zero hour is 1/1/70
      x = 'Thu Jan 01 00:00:00 1970'
      # print("Zero hour = " + x)

      # Convert to a stucture format
      y = time.strptime(x)
      # print("Y = " + str(y))

      #Calculate seconds from GMT zero hour
      z = calendar.timegm(y)
      # print("Zero hour in seconds = " + str(z))

      # All we need is the following
      # Current date and time
      a = datetime.datetime.now()
      # print("Current date and time = " + str(a))

      # Format properly
      b = a.strftime('%a %b %d %H:%M:%S %Y')
      # print("B = " + b)

      # convert to a struct time
      c = time.strptime(b)
      # print("C = " + str(b))

      #Calculate seconds from GMT zero hour
      utcts = calendar.timegm(c)
      # print("Seconds from UTC Zero hour = " + str(utcts))

      hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
      # print("Hashstring = " + hashstring)

      # Assumes the default UTF-8
      hash_object = hashlib.md5(hashstring.encode())
      # print(hash_object.hexdigest())

      # sendtime = datetime.now()
      # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

      url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key="+settings.ADIRONDACK_API_SECRET+"&" \
            "utcts="+str(utcts)+"&" \
            "h="+hash_object.hexdigest()+"&" \
            "AccountCode=2010,2011,2031,2040"
      # print("URL = " + url)

      response = requests.get(url)
      x = json.loads(response.content)
      # print(x)
      y = (len(x['DATA'][0][0]))
      if not x['DATA']:
          print("No match")
      else:
          fn_write_misc_header()
          print("Start Loop")
          # with open('ascii_room_damages.csv', 'ab') as fee_output:

          with codecs.open(settings.ADIRONDACK_ROOM_DAMAGES, 'ab',
                           encoding='utf-8-sig') as fee_output:

              for i in x['DATA']:
                  # print(i[0])

                  # Marietta needs date, description,account number, amount,
                  # ID, totcode, billcode, term
                  rec = str([i[1] + "," + i[5] + ",1-003-10041" + "," +
                             str(i[2]) + "," + str(i[0]) + "," + "S/A" + "," +
                             i[6] + "," + i[4]])

                  print("Rec = " + rec)


                  csvWriter = csv.writer(fee_output,
                                         quoting=csv.QUOTE_NONNUMERIC)
                  csvWriter.writerow([i[1] + "," + i[5] + ",1-003-10041" + ","
                        + str(i[2]) + "," + str(i[0]) + "," + "S/A" + "," +
                        i[6] + "," + i[4]])

    except Exception as e:
          print("Error in adirondack_misc_fees_api.py- Main:  " + e.message)
          # fn_write_error("Error in adirondack_std_billing_api.py - Main: "
          #                + e.message)

if __name__ == "__main__":
    # args = parser.parse_args()
    # test = args.test
    # database = args.database

# if not database:
#     print "mandatory option missing: database name\n"
#     parser.print_help()
#     exit(-1)
# else:
#     database = database.lower()

# if database != 'cars' and database != 'train' and database != 'sandbox':
#     print "database must be: 'cars' or 'train' or 'sandbox'\n"
#     parser.print_help()
#     exit(-1)

    sys.exit(main())
