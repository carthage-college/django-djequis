import calendar
import time
import datetime
import hashlib
import json
import os
import requests
import csv
# prime django
import django
# django settings for script
from django.conf import settings
from djequis.core.utils import sendmail
from adirondack_utilities import fn_write_error, fn_write_application_header, \
    fn_get_utcts

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()

# set up command-line options
desc = """
    Collect adirondack data from applications for housing
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
            "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
            "utcts=" + str(utcts) + "&" \
            "h=" + hash_object.hexdigest() + "&" \
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
        # y = (len(x['DATA'][0][0]))
        if not x['DATA']:
            print("No match")
        else:
            fn_write_application_header()

            print("Start Loop")
            with open(settings.ADIRONDACK_APPLICATONS, 'ab') as output:
                for i in x['DATA']:
                    print(i)
                    csvWriter = csv.writer(output,
                                           quoting=csv.QUOTE_NONNUMERIC)
                    csvWriter.writerow(i)


    except Exception as e:
        print("Error in adirondack_applicationss_api.py- Main:  " + e.message)
        # fn_write_error("Error in adirondack_std_billing_api.py - Main: "
        #                + e.message)


if __name__ == "__main__":
    main()
#     args = parser.parse_args()
#     test = args.test
# sys.exit(main())
