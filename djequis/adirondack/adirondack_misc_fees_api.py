import os
import sys
import time
import datetime
import codecs
import hashlib
import json
import requests
import csv
import logging
import django
from logging.handlers import SMTPHandler
from django.conf import settings
from djequis.core.utils import sendmail
from adirondack_utilities import fn_write_error, fn_write_misc_header, \
    fn_sendmailfees, fn_get_utcts

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django

django.setup()

# django settings for script

# set up command-line options
desc = """
    Collect adirondack fee data for ASCII Post
"""
# Test with this then remove, use the standard logging mechanism
logger = logging.getLogger(__name__)


def main():
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        # print("Hashstring = " + hashstring)

        # Assumes the default UTF-8
        hash_object = hashlib.md5(hashstring.encode())
        # print(hash_object.hexdigest())

        datetimestr = time.strftime("%Y%m%d%H%M%S")

        # Note.  Each account code must be a separate file for ASCII Post
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
              "carthage_thd_test_support/apis/thd_api.cfc?" \
              "method=studentBILLING&" \
              "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
              "utcts=" + str(utcts) + "&" \
              "h=" + hash_object.hexdigest() + "&" \
              "AccountCode=2010"
              # + "&" \
              # "ExportCharges=-1"

        print("URL = " + url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        if not x['DATA']:
            print("No data")
        else:

            fee_file = settings.ADIRONDACK_TXT_OUTPUT + \
                       settings.ADIRONDACK_ROOM_FEES
            fee_archive = settings.ADIRONDACK_ARCHIVED + datetimestr + '_' + \
                          settings.ADIRONDACK_ROOM_FEES

            os.rename(fee_file, fee_archive)

            with codecs.open(fee_file, 'ab',
                             encoding='utf-8-sig') as fee_output:

                for i in x['DATA']:
                    # Marietta needs date, description,account number, amount,
                    # ID, totcode, billcode, term
                    rec = []
                    rec.append(i[1])

                    descr = str(i[5])
                    descr = descr.translate(None, '!@#$%.,')
                    print(descr)

                    rec.append(descr)
                    rec.append("1-003-10041")
                    rec.append(i[2])
                    rec.append(i[0])
                    rec.append("S/A")
                    rec.append(i[6])
                    rec.append(i[4])

                    # print("Rec = " + str(rec))
                    csvWriter = csv.writer(fee_output,
                                           quoting=csv.QUOTE_NONE)
                    csvWriter.writerow(rec)

            # print("File created, send")
            SUBJECT = 'Housing Miscellaneous Fees'
            BODY = 'There are housing fees to process via ASCII post'
            fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
                            settings.ADIRONDACK_FROM_EMAIL,
                            BODY, SUBJECT
                            )

    except Exception as e:
        print("Error in adirondack_misc_fees_api.py- Main:  " + e.message)
        fn_write_error("Error in adirondack_std_billing_api.py - Main: "
                       + e.message)


if __name__ == "__main__":
    sys.exit(main())
