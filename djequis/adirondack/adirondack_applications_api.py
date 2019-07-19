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
from adirondack_utilities import fn_write_error, fn_write_billing_header,\
    fn_write_assignment_header, fn_write_application_header, fn_get_utcts

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
           
      utcts = fn_get_utcts()
      hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
      # print("Hashstring = " + hashstring)

      # Assumes the default UTF-8
      hash_object = hashlib.md5(hashstring.encode())
      print(hash_object.hexdigest())

      # sendtime = datetime.now()
      # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

      url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=housingAPPLICATIONS&" \
            "Key="+settings.ADIRONDACK_API_SECRET+"&" \
            "utcts="+str(utcts)+"&" \
            "h="+hash_object.hexdigest()+"&" \
            "TimeFrameNumericCode=" + "RA 2019"
            # + "&" \
            # "studentNumber=-1"
            # + "&"
            # "ApplicationTypeName= "
              # + "&"
              # "APP_COMPLETE= "
              # + "&"
              # "APP_CANCELED= "
              # + "&"
              # "DEPOSIT= "
              # + "&"
              # "UNDERAGE= "

      # print("URL = " + url)

      response = requests.get(url)
      x = json.loads(response.content)
      # print(x)
      y = (len(x['DATA'][0][0]))
      if not x['DATA']:
          print("No match")
      else:
          fn_write_application_header()
          print("Start Loop")
          with open(settings.ADIRONDACK_APPLICATONS, 'ab') as output:
              for i in x['DATA']:
                  rec = []
                  rec.append(i[0])
                  rec.append(i[1])
                  rec.append(i[2])
                  rec.append(i[3])
                  rec.append(i[4])
                  rec.append(i[5])
                  rec.append(i[6])
                  rec.append(i[7])
                  rec.append(i[8])
                  rec.append(i[9])
                  rec.append(i[10])
                  rec.append(i[11])
                  rec.append(i[12])
                  rec.append(i[13])
                  rec.append(i[14])
                   # print("Rec = " + str(rec))
                  csvWriter = csv.writer(output,
                                         quoting=csv.QUOTE_NONNUMERIC)
                  csvWriter.writerow(rec)

          # Validate if the stu_serv_rec exists first                            ])
          # update stu_serv_rec id, sess, yr, rxv_stat, intend_hsg, campus, bldg, room, bill_code


    except Exception as e:
          print("Error in adirondack_applicationss_api.py- Main:  " + e.message)
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
