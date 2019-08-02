import os
# import glob
import shutil
import sys
import time
import datetime
from datetime import datetime, timedelta
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
    #Working Assumptions:
    # We will do a mass pull around April 20 when the returning students
    # have been assigned.
    # New Students will be assigned after that, but since Marietta only bills
    # in July, it won't matter what changes or doesn't - nothing has been
    # billed
    # So after April 20, we will just do daily updates.  Whatever she bills
    # on April 20 will then have to be tracked for new entries and for
    # room changes.   The process can run daily for the rest of the year

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
            + "&" + "ExportCharges=-1"
        # \
        #     + "&" + "STUDENTNUMBER=ASI000987654321"

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
            # Cleanup previous run CSV files
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

            # How to know if a record has already been processed?
            # The 'EXPORTED' flag may not be useful.
            # If it was exported, it does not follow that it has been
            # processed.  Maybe look for recent records by date
            # of the incident, process those and skip the others
            # But how far to look back?
            # Should I also compare to previous CSV a la ADP?
            # Or can I use the STUDENTBILLINGINTERNALID number somehow?
            # Store the numbers in a txt file AFTER the csv has been
            # successfully created, read that file into a list and if
            # the new data pulls the same number, pass through

            # testlist = ['2', '968', '069']
            # Temporary
            f = open("Assignment_id_lst.txt", "r")
            contents = f.read()
            print(contents)
            testlist = []
            for row in contents:
                testlist.append(row[0])

            for i in x['DATA']:
                #--------------------
                # Validation Option 1
                rec_id = str(i[16])
                print("STUDENTBILLINGINTERNALID = " + rec_id)
                if rec_id in testlist:
                    print("Matched to list...")
                #--------------------


                # Marietta needs date, description,account number, amount,
                # ID, totcode, billcode, term

                item_date = datetime.strptime(i[1], '%m/%d/%Y')
                print(item_date)

                #--------------------
                # Validation Option 2 uses EXPORTED flag, but is unreliable
                print(i[9])
                if i[9] == -1:
                    print("File was previously exported")
                else:
                    print("File fresh")
                #--------------------


                filter_date = datetime.now() - timedelta(days=90)
                print(filter_date)
                if item_date >= filter_date:
                    print('OK')

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

                    fee_file = settings.ADIRONDACK_TXT_OUTPUT + totcode \
                               + "_" + settings.ADIRONDACK_ROOM_FEES \
                               + datetimestr + ".csv"

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
                    # fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
                    #                 settings.ADIRONDACK_FROM_EMAIL,
                    #                 BODY, SUBJECT
                    #                 )

                else:
                    print("OLD Don't process")

    except Exception as e:
        print("Error in adirondack_misc_fees_api.py- Main:  " + e.message)
        fn_write_error("Error in adirondack_std_billing_api.py - Main: "
                   + e.message)

if __name__ == "__main__":
    sys.exit(main())
