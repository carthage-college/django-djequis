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
from adirondack_utilities import fn_write_error, fn_write_billing_header, \
    fn_write_assignment_header

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
        # GMT Zero hour is 1/1/70
        x = 'Thu Jan 01 00:00:00 1970'
        # Convert to a stucture format
        y = time.strptime(x)
        # Calculate seconds from GMT zero hour
        # z = calendar.timegm(y)
        # print("Zero hour in seconds = " + str(z))
        # Current date and time
        a = datetime.datetime.now()
        # Format properly
        b = a.strftime('%a %b %d %H:%M:%S %Y')
        # convert to a struct time
        c = time.strptime(b)
        # print("C = " + str(b))
        # Calculate seconds from GMT zero hour
        utcts = calendar.timegm(c)
        # print("Seconds from UTC Zero hour = " + str(utcts))
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        # print("Hashstring = " + hashstring)

        # Assumes the default UTF-8
        hash_object = hashlib.md5(hashstring.encode())
        print(hash_object.hexdigest())
        # sendtime = datetime.now()
        # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))

        url = "https://carthage.datacenter.adirondacksolutions.com/" \
              "carthage_thd_test_support/apis/thd_api.cfc?" \
              "method=housingASSIGNMENTS&" \
              "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
                                                        "utcts=" + str(
            utcts) + "&" \
                     "h=" + hash_object.hexdigest() + "&" \
                                        "TimeFrameNumericCode=" + "RA 2019"
        # + "&" \
        # "CurrentFuture=-1"
        # + "&"
        # "HallCode=DEN,JOH,OAKS1,OAKS2,OAKS3,OAKS4,OAKS5,OAKS6,MADR,SWE," \
        #     "TAR,TOWR,UN,OFF,ABRD,CMTR,''"

        # print("URL = " + url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        y = (len(x['DATA'][0][0]))
        if not x['DATA']:
            print("No match")
        else:
            fn_write_assignment_header()
            print("Start Loop")
            with open(settings.ADIRONDACK_ROOM_ASSIGNMENTS,
                      'ab') as room_output:
                for i in x['DATA']:
                    carthid = i[0]
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
                    rec.append(i[15])
                    rec.append(i[16])
                    rec.append(i[17])
                    rec.append(i[18])
                    rec.append(i[19])
                    rec.append(i[20])
                    rec.append(i[21])
                    rec.append(i[22])

                    # print("Rec = " + str(rec))
                    csvWriter = csv.writer(room_output,
                                           quoting=csv.QUOTE_NONE)
                    csvWriter.writerow(rec)

            # Validate if the stu_serv_rec exists first
            # ])
            # update stu_serv_rec id, sess, yr, rxv_stat, intend_hsg,
            # campus, bldg, room, bill_code
            q_validate_stuserv_rec = '''
                          select id, sess, yr, rsv_stat, 
                          intend_hsg, campus, bldg, room, no_per_room, 
                          add_date, 
                          bill_code, hous_wd_date 
                          from stu_serv_rec 
                          where id = {0}'''.format(carthid)
            print(q_validate_stuserv_rec)

            # NOTE ABOUT WITHDRAWALS!!!!
            # Per Amber, the only things that get changed when a student
            # withdraws
            # are setting the rsv_stat to "W' and the bill_code to "NOCH"
            # if action == 'A':
            #     print("Add")
            #     rsvstat = 'R'
            #     billcode = "STD"
            # else:
            #     print("Remove")
            #     rsvstat = 'W'
            #     billcode = "NOCH"

                # # Insert if no record exists, update else
                # q_insert_stuserv_rec = '''
                #         INSERT INTO stu_serv_rec (id, sess, yr, rsv_stat,
                #         intend_hsg, campus, bldg, room, no_per_room,
                #         add_date,
                #         bill_code, hous_wd_date)
                #         VALUES (?,?,?,?,?,?,?,?,?,?,?)'''
                # q_insert_stuserv_args = (
                #       carthid, term, yr, rsvstat, 'R', 'MAIN', building,
                #       room, occupants,
                #       startdate, billcode, enddate)
                # print(q_insert_stuserv_rec)
                # print(q_insert_stuserv_args)
                # # engine.execute(q_insert_stuserv_rec, q_insert_stuserv_args)

                # filepath = settings.ADIRONDACK_CSV_OUTPUT

            # q_update_stuserv_rec = '''
            #               UPDATE stu_serv_rec set  rsv_stat = ?,
            #               intend_hsg = ?, campus = ?, bldg = ?, room = ?,
            #               no_per_room = ?, add_date = ?, bill_code = ?,
            #               hous_wd_date = ?)
            #               where id = ? and sess = ? and yr = ?'''
            # q_update_stuserv_args = (rsvstat, 'MAIN', building, room,
            # occupants,
            #     startdate, billcode, enddate, carthid, term, yr, 'R')
            # print(q_update_stuserv_rec)
            # print(q_update_stuserv_args)





    except Exception as e:
        print(
                    "Error in adirondack_room_assignments_api.py- Main:  " +
                    e.message)
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
