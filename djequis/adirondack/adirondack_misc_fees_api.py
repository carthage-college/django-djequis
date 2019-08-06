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


from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from django.conf import settings
from django.db import connections

from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

#
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
# informix environment
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH



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


def fn_set_terms(last_term, current_term):
    trmqry = '''select trim(sess)||yr as cur_term, acyr, 
                        ROW_NUMBER () OVER () as rank
                        from train:acad_cal_rec a
                        where  yr = YEAR(TODAY)
                        and (right(acyr,2) = RIGHT(TO_CHAR(YEAR(TODAY)),2) 
                        or left(acyr, 2) = RIGHT(TO_CHAR(YEAR(TODAY)),2))  
                        and sess in ('RC', 'RA')
                        AND subsess = ''
                        and prog = 'UNDG'
                        order by beg_date asc
                        '''
    # print(trmqry)

    ret = do_sql(trmqry, earl=EARL)

    if ret is not None:
        for row in ret:
            if row[2] == '1':
                last_term = row[0]
            else:
                current_term = row[0]

    return [last_term, current_term]

def main():
    # set global variable
    global EARL
    # determines which database is being called from the command line
    EARL = INFORMIX_EARL_TEST
    # establish database connection
    engine = get_engine(EARL)

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

            # I need a way to only compare exported items to fairly recent
            # posted items, or the list will get huge.


            # ------------------------------------------
            # Step 1 would be to build the list of items already written to
            # a csv for the terms
            # ------------------------------------------

            last_term, current_term = fn_set_terms('', '')
            # print("new last = " + last_term)
            # print("new current = " + current_term)

            cur_file = current_term + '_processed.csv'
            last_file = last_term + '_processed.csv'

            the_list = []

            if os.path.isfile(cur_file):
                # print ("Curfile exists")
                f = current_term + '_processed.csv'
                with open(f, 'r') as ffile:
                    csvf = csv.reader(ffile)
                    # File should have two columns, one for term and one for row
                    # id from
                    # Adirondack.
                    for row in csvf:
                        # term = row[0]
                        assign_id = int(row[3].strip())
                        the_list.append(assign_id)
                ffile.close()

            else:
                print ("No file")
                with open(cur_file, "w") as empty_csv:
                    pass

            if os.path.isfile(last_file):
                # print ("last_file exists")
                l = last_term + '_processed.csv'
                with open(l, 'r') as ffile:
                    csvl = csv.reader(ffile)
                    for row in csvl:
                        # term = row[0]
                        assign_id = int(row[3].strip())
                        the_list.append(assign_id)
                ffile.close()

            else:
                print ("No file")
                with open(last_file, "w") as empty_csv:
                    pass

            print(the_list)

            # ------------------------------------------
            #  Step 2 would be to get the new charges from adirondack
            #  this will be the API query
            # ------------------------------------------


            for i in x['DATA']:
                # --------------------
                # Validation Option 1
                # Store a list of record ids from Adirondack for the term
                # AFTER the csv has been successfully created
                # Compare each new file's line ID

                adir_term = i[4][:2] + i[4][-4:]
                bill_id = str(i[16])
                stu_id = str(i[0])
                tot_code = str(i[6])

                print("Adirondack term to check = " + adir_term)
                print("CX Current Term = " + current_term)

                if current_term == adir_term:
                    print("Match current term " + current_term)
                    # here we look for a specific item

                    print(the_list)
                    if int(bill_id) in the_list:
                        print("Item " + bill_id + " already in list")
                    else:
                        print("Write item " + str(
                            i[16]) + " to current term file")
                        f = current_term + '_processed.csv'
                        lin = []
                        lin.append(adir_term)
                        lin.append(stu_id)
                        lin.append(tot_code)
                        lin.append(bill_id)
                        print(lin)

                        with codecs.open(f, 'ab',
                                         encoding='utf-8-sig') as wffile:
                            csvWriter = csv.writer(wffile,
                                                   quoting=csv.QUOTE_MINIMAL)
                            csvWriter.writerow(lin)
                        wffile.close()

                else:
                    print(the_list)
                    # print("Match last term " + last_term)
                    if int(i[16]) in the_list:
                        print("Item " + str(i[16]) + " already in list")
                    else:
                        print("Write item " + str(
                            i[16]) + " to last term file")


                # Marietta needs date, description,account number, amount,
                # ID, totcode, billcode, term
                item_date = datetime.strptime(i[1], '%m/%d/%Y')
                print(item_date)




                    # print("File created, send")
                    # SUBJECT = 'Housing Miscellaneous Fees'
                    # BODY = 'There are housing fees to process via ASCII post'
                    # fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
                    #                 settings.ADIRONDACK_FROM_EMAIL,
                    #                 BODY, SUBJECT
                    #                 )

                # else:
                #     print("OLD Don't process")

    except Exception as e:
        print("Error in adirondack_misc_fees_api.py- Main:  " + e.message)
        fn_write_error("Error in adirondack_std_billing_api.py - Main: "
                   + e.message)

if __name__ == "__main__":
    sys.exit(main())
