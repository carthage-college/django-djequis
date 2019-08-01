import os
# import glob
import shutil
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

        datetimestr = time.strftime("%Y%m%d")
        timestr = time.strftime("%H%M")
        # print(timestr)

        # Note.  Each account code must be a separate file for ASCII Post
        # Only FINE Sample fine
        # 2010  Improper Checkout
        # 2011  Extended stay charge
        # 2031   Recore
        # 2040  Lockout fee
        # All others are room charges not for ASCII post
        # Should I  modularize the URL and make four calls?
        # Or should I write four separate files by filtering the return in
        # the loop?
        # Since there is no header, the latter may work best
        # Would need to delete all, write whatever comes back, test for
        # existence of each and mail each
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
            "utcts=" + str(utcts) + "&" \
            "h=" + hash_object.hexdigest() + "&" \
            "AccountCode=2010,2040,2011,2031" \
            + "&" + "Exported=0" \
            + "&" + "ExportCharges=-1" \
            + "&" + "STUDENTNUMBER=ASI000987654321"

            # DEFINIIONS
            # Exported: -1 exported will be included, 0 only non-exported
            # ExportCharges: if -1 then charges will be marked as exported

            # print("URL = " + url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        if not x['DATA']:
            print("No new data found")
        else:
            files = os.listdir(settings.ADIRONDACK_TXT_OUTPUT)

            for f in files:
                if f.find('misc_housing') != -1:
                    ext = f.find(".csv")

                    # print("source = " + settings.ADIRONDACK_TXT_OUTPUT+f)
                    # print("destintation = " + settings.ADIRONDACK_ARCHIVED+
                    # f[:ext]
                    # + "_" + timestr + f[ext:])
                    shutil.move(settings.ADIRONDACK_TXT_OUTPUT + f,
                                settings.ADIRONDACK_ARCHIVED + f[:ext] + "_" +
                                timestr + f[ext:])

            for i in x['DATA']:
                # Marietta needs date, description,account number, amount,
                # ID, totcode, billcode, term
                rec = []
                rec.append(i[1])
                descr = str(i[5])
                descr = descr.translate(None, '!@#$%.,')
                rec.append(descr.strip())
                rec.append("1-003-10041")
                rec.append(i[2])
                rec.append(i[0])
                rec.append("S/A")
                totcode = i[6]
                # print(totcode)
                rec.append(totcode)
                rec.append(i[4][:2] + i[4][5:])

                fee_file = settings.ADIRONDACK_TXT_OUTPUT + totcode + "_" + \
                           settings.ADIRONDACK_ROOM_FEES + datetimestr + ".csv"

                # print(fee_file)
                with codecs.open(fee_file, 'ab',
                                 encoding='utf-8-sig') as fee_output:
                    csvWriter = csv.writer(fee_output,
                                           quoting=csv.QUOTE_NONE)
                    csvWriter.writerow(rec)
                fee_output.close()

                print("File created, send")
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
