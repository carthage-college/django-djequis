import calendar
import time
import datetime
import hashlib
import json
import os
import requests
import csv

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
import django
django.setup()

# django settings for script
from django.conf import settings
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from adirondack_sql import ADIRONDACK_QUERY
from utilities import fn_write_error, fn_write_billing_header

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

# set up command-line options
desc = """
    Collect adirondack data ASCII Post
"""

print("x")

def encode_rows_to_utf8(rows):
    encoded_rows = []
    for row in rows:
        try:
            encoded_row = []
            for value in row:
                if isinstance(value, basestring):
                    value = value.decode('cp1252').encode("utf-8")
                encoded_row.append(value)
            encoded_rows.append(encoded_row)
        except Exception as e:
            fn_write_error("Error in encoded_rows routine " + e.message)
    return encoded_rows


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
      print("Zero hour in seconds = " + str(z))

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
      print("Seconds from UTC Zero hour = " + str(utcts))
      hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
      print("Hashstring = " + hashstring)

      # mystring = 'Enter String to hash'
      # Assumes the default UTF-8
      hash_object = hashlib.md5(hashstring.encode())
      print(hash_object.hexdigest())

      # sendtime = datetime.now()
      # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

      url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key="+settings.ADIRONDACK_API_SECRET+"&" \
            "utcts="+str(utcts)+"&" \
            "h="+hash_object.hexdigest()+"&" \
            "AccountCode=CMTR,ABRD,NOCH,UNDE,OFF,RABD,RFDB,RFPB,RFOD,RFOS,RFQU,RFT2,CCHI,STD,RFSG,RFTR,RFTD,RFTS,RFAP" +"&" \
            "STUDENTNUMBER=1431381"
      print("URL = " + url)

      response = requests.get(url)
      x = json.loads(response.content)
      # print(x)
      y = (len(x['DATA'][0][0]))
      if not x['DATA']:
          print("No match")
      else:
          filename = settings.ADIRONDACK_ROOM_FEES + ".csv"
          fn_write_billing_header(filename)
          print("Start Loop")
          with open(filename, 'ab') as room_output:
              for i in x['DATA']:
                  print(i[0])
                  csvWriter = csv.writer(room_output, quoting=csv.QUOTE_NONNUMERIC)
                  csvWriter.writerow([i[0] + ',' + i[1] + ',' + str(i[2]) + ','
                  + str(i[3]) + ',' + i[4] + ',' + i[5] + ','
                  + i[6] + ',' + i[7] + ',' + i[8] + ','
                  + str(i[9]) + ',' + str(i[10]) + ','
                  + str(i[11]) + ',' + str(i[12]) + ','
                  + str(i[13]) + ',' + str(i[14]) + ','
                  + str(i[15]) + ',' + str(i[16]) + ','
                  + str(i[17]) + ',' + str(i[18])
                          ])


    except Exception as e:
          print("Error in adirondack_std_billing_api.py- Main:  " + e.message)
          # fn_write_error("Error in adirondack_std_billing_api.py - Main: "
          #                + e.message)

if __name__ == "__main__":
    main()
#     args = parser.parse_args()
#     test = args.test
#     database = args.database
#
# if not database:
#     print "mandatory option missing: database name\n"
#     parser.print_help()
#     exit(-1)
# else:
#     database = database.lower()
#
# if database != 'cars' and database != 'train' and database != 'sandbox':
#     print "database must be: 'cars' or 'train' or 'sandbox'\n"
#     parser.print_help()
#     exit(-1)
#
# sys.exit(main())
