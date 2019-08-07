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
    fn_sendmailfees, fn_get_utcts, fn_write_billing_header

from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from django.conf import settings
from django.db import connections

from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
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

            # How to know if a record has already been processed to
            #    avoid duplicates?
            # Use the STUDENTBILLINGINTERNALID number
            #    Store the numbers in a txt file
            #    read that file into a list and
            #    if the new data pulls the same ID number, pass through
            #    I need a way to only compare exported items to fairly recent
            #    posted items, or the list will get huge.

            # ------------------------------------------
            # Step 1 would be to build the list of items already written to
            # a csv for the terms
            # ------------------------------------------

            # Figure out what terms to limit to
            last_term, current_term = fn_set_terms('', '')
            # print("new last = " + last_term)
            # print("new current = " + current_term)

            # Set up the file names for the duplicate check
            cur_file = current_term + '_processed.csv'
            last_file = last_term + '_processed.csv'
            # print(cur_file)
            # print(last_file)

            # Initialize a list of record IDs
            the_list = []

            # Make sure file for the current term has been created
            if os.path.isfile(cur_file):
                print ("Curfile exists")
                f = current_term + '_processed.csv'

                with open(f, 'r') as ffile:
                    csvf = csv.reader(ffile)
                    #the [1:] skips header
                    # File should have at least columns for term row ID
                    next(ffile)
                    for row in csvf:
                        if row is not None:
                            assign_id = int(row[16].strip())
                            the_list.append(assign_id)
                ffile.close()
            else:
                print ("No file")
                fn_write_billing_header(cur_file)
                # with open(cur_file, "w") as empty_csv:
                #     pass

            # For extra insurance, include last term items in the list
            if os.path.isfile(last_file):
                # print ("last_file exists")
                l = last_term + '_processed.csv'
                with open(l, 'r') as lfile:
                    csvl = csv.reader(lfile)  #the [1:] skips header
                    next(lfile)
                    for row in csvl:
                        # term = row[0]
                        assign_id = int(row[16].strip())
                        the_list.append(assign_id)
                lfile.close()
            else:
                print ("No file")
                fn_write_billing_header(last_file)
                # with open(last_file, "w") as empty_csv:
                #     pass

            # List of processed rows
            print(the_list)


            # ------------------------------------------
            #  Step 2 would be to loop through the new charges from adirondack
            #  in the API query
            # ------------------------------------------

            # Note.  Each account code must be a separate file for ASCII Post
            # Only FINE Sample fine
            # 2010  Improper Checkout
            # 2011  Extended stay charge
            # 2031   Recore
            # 2040  Lockout fee
            # All others are room charges not for ASCII post

            for i in x['DATA']:
                # print(i)
                # --------------------
                # As the csv is being created
                # Compare each new file's line ID

                # variables for readability
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
                        print("Write to ASCII csv file")
                        rec = []
                        rec.append(i[1])
                        descr = str(i[5])
                        descr = descr.translate(None, '!@#$%.,')
                        rec.append(descr.strip())
                        rec.append("1-003-10041")
                        rec.append(i[2])
                        rec.append(stu_id)
                        rec.append("S/A")
                        rec.append(tot_code)
                        rec.append(adir_term)

                        fee_file = settings.ADIRONDACK_TXT_OUTPUT + tot_code \
                                   + "_" + settings.ADIRONDACK_ROOM_FEES \
                                   + datetimestr + ".csv"

                        # print(fee_file)
                        with codecs.open(fee_file, 'ab',
                                         encoding='utf-8-sig') as fee_output:
                            csvWriter = csv.writer(fee_output,
                                                   quoting=csv.QUOTE_NONE)
                            csvWriter.writerow(rec)
                        fee_output.close()

                        # Write record of item to PROCESSED list
                        # NOTE--QUOTE_MINIMAL is because timestamp has a comma
                        print("Write item " + str(
                            i[16]) + " to current term file")
                        f = current_term + '_processed.csv'
                        # print(i)
                        with codecs.open(f, 'ab',
                                         encoding='utf-8-sig') as wffile:
                            csvWriter = csv.writer(wffile,
                                                   quoting=csv.QUOTE_MINIMAL)
                            csvWriter.writerow(i)
                        wffile.close()

                        print("File created, send")
                        SUBJECT = 'Housing Miscellaneous Fees'
                        BODY = 'There are housing fees to process via ASCII ' \
                               'post'
                        # fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
                        #                 settings.ADIRONDACK_FROM_EMAIL,
                        #                 BODY, SUBJECT
                        #                 )

                else:
                    # In case of a charge from the previous term
                    print(the_list)
                    # print("Match last term " + last_term)
                    if int(i[16]) in the_list:
                        print("Item " + str(i[16]) + " already in list")
                    else:

                        print("Write to ASCII csv file")
                        rec = []
                        rec.append(i[1])
                        descr = str(i[5])
                        descr = descr.translate(None, '!@#$%.,')
                        rec.append(descr.strip())
                        rec.append("1-003-10041")
                        rec.append(i[2])
                        rec.append(stu_id)
                        rec.append("S/A")
                        rec.append(tot_code)
                        rec.append(adir_term)

                        fee_file = settings.ADIRONDACK_TXT_OUTPUT + tot_code \
                                   + "_" + settings.ADIRONDACK_ROOM_FEES \
                                   + datetimestr + ".csv"

                        # print(fee_file)
                        with codecs.open(fee_file, 'ab',
                                         encoding='utf-8-sig') as fee_output:
                            csvWriter = csv.writer(fee_output,
                                                   quoting=csv.QUOTE_NONE)
                            csvWriter.writerow(rec)
                        fee_output.close()

                        #Write record of item to PROCESSED list
                        # NOTE--QUOTE_MINIMAL is because timestamp has a comma
                        print("Write item " + str(
                            i[16]) + " to current term file")
                        f = current_term + '_processed.csv'
                        with codecs.open(f, 'ab',
                                         encoding='utf-8-sig') as wffile:
                            csvWriter = csv.writer(wffile,
                                                   quoting=csv.QUOTE_MINIMAL)
                            csvWriter.writerow(i)
                        wffile.close()

                        print("File created, send")
                        SUBJECT = 'Housing Miscellaneous Fees'
                        BODY = 'There are housing fees to process via ASCII ' \
                               'post'
                        # fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
                        #                 settings.ADIRONDACK_FROM_EMAIL,
                        #                 BODY, SUBJECT
                        #                 )



                # Marietta needs date, description,account number, amount,
                # ID, tot_code, billcode, term
                item_date = datetime.strptime(i[1], '%m/%d/%Y')
                print(item_date)


            # When all done, email csv file?
            # Or notify and write file to a directory somewhere?
            # Ideally, write to Wilson into fin_post directory
            # print("File created, send")
            # SUBJECT = 'Housing Miscellaneous Fees'
            # BODY = 'There are housing fees to process via ASCII post'
            # fn_sendmailfees(settings.ADIRONDACK_TO_EMAIL,
            #                 settings.ADIRONDACK_FROM_EMAIL,
            #                 BODY, SUBJECT
            #                 )


    except Exception as e:
        print("Error in adirondack_misc_fees_api.py- Main:  " + e.message)
        fn_write_error("Error in adirondack_std_billing_api.py - Main: "
                   + e.message)

if __name__ == "__main__":
    sys.exit(main())
