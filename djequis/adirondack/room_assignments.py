import hashlib
import json
import os
import sys
import time
import datetime
from datetime import datetime
import requests
import csv
import argparse
import django
# ________________
# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()
# ________________

from django.conf import settings
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djtools.fields import TODAY
from djzbar.settings import INFORMIX_EARL_SANDBOX
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD
from adirondack_sql import ADIRONDACK_QUERY
from utilities import fn_write_error, fn_write_billing_header, \
    fn_write_assignment_header, fn_get_utcts, fn_encode_rows_to_utf8

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
    Collect adirondack data Room assignments for stu_serv_rec
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
parser.add_argument(
    "-d", "--database",
    help="database name.",
    dest="database"
)


def fn_get_bill_code(idnum, bldg, roomtype, roomassignmentid, session):
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        hash_object = hashlib.md5(hashstring.encode())
        print(session)
        print(bldg)
        print(idnum)
        print(roomtype)
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key=" + settings.ADIRONDACK_API_SECRET + "&" + "utcts=" + \
            str(utcts) + "&" + "h=" + \
            hash_object.hexdigest() + "&" + \
            "ASSIGNMENTID=" + str(roomassignmentid) + "&" + \
            "TIMEFRAMENUMERICCODE=" + session

        # "ItemType=" + roomtype.strip() + "&" + \
        # __"STUDENTNUMBER=" + idnum + "&" + \
        #             _____________________________
        # Need to dynamically get the term - see the misc fee file
        # _______________________________
        # print(url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        if not x['DATA']:
            print("No data")
            if bldg == 'CMTR':
                billcode = 'CMTR'
            elif bldg == 'OFF':
                billcode = 'OFF'
            elif bldg == 'ABRD':
                billcode = 'ABRD'
            else:
                billcode = ''
            print("Billcode found as " + billcode)
            return billcode
        else:
            for rows in x['DATA']:
                print(rows)
                # print("ASSIGNMENTID = " + str(rows[14]))
                # print("Room Assignment ID search = " + str(roomassignmentid))
                if roomassignmentid == rows[14]:
                    print(rows[6])
                    billcode = rows[6]
                    print("Billcode found as " + billcode)
                    return billcode
    except Exception as e:
        print(
                "Error in adirondack_room_assignments_api.py- "
                "fn_get_bill_code:  " + e.message)
        fn_write_error("Error in adirondack_std_billing_api.py "
                       "- fn_get_bill_code: " + e.message)


def fn_fix_bldg(bldg_code):
    if bldg_code[:3] == 'OAK':
        x = bldg_code.replace(" ", "")
        l = len(bldg_code.strip())
        b = bldg_code[l - 1:l]
        z = x[:3]
        bldg = z + b
        # print(bldg)
        return bldg
    else:
        return bldg_code

def fn_mark_posted(stu_id, room_no, hall_code, term):
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        hash_object = hashlib.md5(hashstring.encode())


        print("In fn_mark_posted " + str(stu_id) + ", " + str(room_no) + ", "
              + str(hall_code) + ", " + term)
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            "carthage_thd_test_support/apis/thd_api.cfc?" \
            "method=housingASSIGNMENTS&" \
            "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
            "utcts=" + \
            str(utcts) + "&" \
            "h=" + hash_object.hexdigest() + "&" \
            "TimeFrameNumericCode=" + term + "&" \
            "CurrentFuture=-1" + "&" \
            "Ghost=0" + "&" \
            "STUDENTNUMBER=" + stu_id + "&" \
            "PostAssignments=-1" + "&" \
            "HallCode=" + hall_code + "&" \
            "Posted=0"
        

        # "RoomNumber=" + room_no + "&" \
        # Room number won't work for off campus types - Room set to CMTR, ABRD
        # etc. in CX.
        # + "&" \
        # print(url)

        # DEFINITIONS
        # Posted: 0 returns only NEW unposted,
        #         1 returns posted, as in export out to our system
        #         2 changed or cancelled
        # PostAssignments: -1 will mark the record as posted.
        # CurrentFuture: -1 returns only current and future
        # Cancelled: -1 is for cancelled, 0 for not cancelled
        # Setting Ghost to -1 prevents rooms with no student from returning
        # print("URL = " + url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        if not x['DATA']:
            print("Unable to mark record as posted - record not found")
        else:
            print("Record marked as posted")

    except Exception as e:
        print("Error in room_assignments_api.py- fn_mark_posted:  " +
              e.message)
        # fn_write_error("Error in room_assignments_api.py- fn_mark_posted:
        # " + e.message)


def main():
    try:
        # if JUNE or JULY
        #     run only on certain days
        # One big push for returning students
        # second big push for freshmen
        # Then run daily starting on...

        # set global variable
        global EARL
        # determines which database is being called from the command line
        # if database == 'cars':
        # EARL = INFORMIX_EARL_PROD
        if database == 'train':
            EARL = INFORMIX_EARL_TEST
        elif database == 'sandbox':
            EARL = INFORMIX_EARL_SANDBOX
        else:
            # # this will raise an error when we call get_engine()
            # below but the argument parser should have taken
            # care of this scenario and we will never arrive here.
            EARL = None
            # establish database connection

        engine = get_engine(EARL)

        # try:

        utcts = fn_get_utcts()
        # print("Seconds from UTC Zero hour = " + str(utcts))
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        # print("Hashstring = " + hashstring)

        # Assumes the default UTF-8
        hash_object = hashlib.md5(hashstring.encode())
        # print(hash_object.hexdigest())
        # print("Time of send = " + time.strftime("%Y%m%d%H%M%S"))
        datetimestr = time.strftime("%Y%m%d%H%M%S")

        q_get_term = '''select trim(trim(sess)||' '||trim(TO_CHAR(yr))) session
                        from acad_cal_rec
                        where sess in ('RA','RC')
                        and subsess = ''
                        and first_reg_date < TODAY
                        and charge_date > TODAY
                         '''
        ret = do_sql(q_get_term, key=DEBUG, earl=EARL)
        # ret = do_sql(q_get_term, earl=EARL)
        if ret is not None:
            row = ret.fetchone()
            if row is None:
                print("Term not found")
            else:
                session = row[0]
                print("Session = " + session)
                # IMPORTANT! won't work if string has any spaces.  NO SPACES

                url = "https://carthage.datacenter.adirondacksolutions.com/" \
                    "carthage_thd_test_support/apis/thd_api.cfc?" \
                    "method=housingASSIGNMENTS&" \
                    "Key=" + settings.ADIRONDACK_API_SECRET + "&" \
                    "utcts=" + \
                    str(utcts) + "&" \
                    "h=" + hash_object.hexdigest() + "&" \
                    "TimeFrameNumericCode=" + session + "&" \
                    "CurrentFuture=-1" + "&" \
                    "Ghost=0" + "&" \
                    "STUDENTNUMBER=" + "1480143"

                # DO NOT MARK AS POSTED HERE - DO IT IN SECOND STEP
                # "PostAssignments=-1" + "&" \
                # "Posted=1" + "&" \
                # + "&" \
                # "HallCode=" + 'SWE'

                # DEFINITIONS
                # Posted: 0 returns only NEW unposted,
                # 1 returns posted, as in out to our system
                # 2 changed or cancelled
                # PostAssignments: -1 will mark the record as posted.
                # CurrentFuture: -1 returns only current and future
                # Cancelled: -1 is for cancelled, 0 for not cancelled

                # print("URL = " + url)

                # In theory, every room assignment in Adirondack should have
                # a bill code

                response = requests.get(url)
                x = json.loads(response.content)
                # print(x)
                if not x['DATA']:
                    print("No new data found")
                else:
                    room_file = settings.ADIRONDACK_TXT_OUTPUT + \
                                settings.ADIRONDACK_ROOM_ASSIGNMENTS + '.csv'
                    # print(room_file)
                    room_archive = settings.ADIRONDACK_ROOM_ARCHIVED + \
                        settings.ADIRONDACK_ROOM_ASSIGNMENTS + \
                        datetimestr + '.csv'
                    # print(room_archive)

                    if os.path.exists(room_file):
                        os.rename(room_file, room_archive)

                    # IF directly updating stu_serv_rec, writing csv may be
                    # redundant
                    fn_write_assignment_header()
                    room_data = fn_encode_rows_to_utf8(x['DATA'])
                    print("Start Loop")

                    with open(room_file, 'ab') as room_output:
                        for i in room_data:
                            print("______")
                            print(i[0])
                            carthid = i[0]
                            bldgname = i[1]
                            adir_hallcode = i[2]
                            bldg = fn_fix_bldg(i[2])
                            print("Adirondack Hall Code = " + adir_hallcode)
                            floor = i[3]
                            bed = i[5]
                            room_type = i[6]
                            occupancy = i[7]
                            roomusage = i[8]
                            timeframenumericcode = i[9]
                            checkin = i[10]
                            if i[11] == None:
                                checkedindate = None
                            else:
                                d1 = datetime.strptime(i[11],
                                                       "%B, "
                                                       "%d %Y "
                                                       "%H:%M:%S")
                                checkedindate = d1.strftime("%m-%d-%Y")
                            # print("ADD DATE = " + str(checkedindate))
                            checkout = i[12]
                            if i[13] == None:
                                checkedoutdate = None
                            else:
                                d1 = datetime.strptime(i[13],
                                                       "%B, "
                                                       "%d %Y "
                                                       "%H:%M:%S")
                                checkedoutdate = d1.strftime("%m-%d-%Y")
                            # print("OUT DATE = " + str(checkedoutdate))
                            po_box = i[14]
                            po_box_combo = i[15]
                            canceled = i[16]
                            canceldate = i[17]
                            cancelnote = i[18]
                            cancelreason = i[19]
                            ghost = i[20]
                            posted = i[21]
                            roomassignmentid = i[22]
                            sess = i[9][:2]
                            year = i[9][-4:]
                            term = i[9]
                            occupants = i[7]
                            billcode = fn_get_bill_code(carthid, str(bldg),
                                                        room_type,
                                                        roomassignmentid,
                                                        session)
                            # print("Bill Code =  " + billcode)
                            # Intenhsg can b R = Resident, O = Off-Campus,
                            # C = Commuter
                            # print(bldgname)
                            # print(bldgname.find('_'))
                            # print(bldgname[(bldgname.find('_') + 1)
                            #       - len(bldgname):])
                            # print(len(bldgname))

                            # This if routine is needed because the adirondack
                            # hall codes match to multiple descriptions and
                            # hall descriptions have added qualifiers such as
                            # FOFF, MOFF, UNF, LOCA that are not available
                            # elsewhere using the API.  Have to parse it to
                            # assign a generic room

                            if bldg == 'CMTR':
                                intendhsg = 'C'
                                room = bldgname[(bldgname.find('_') + 1)
                                                - len(bldgname):]
                            elif bldg == 'OFF':
                                intendhsg = 'O'
                                room = bldgname[(bldgname.find('_') + 1)
                                                - len(bldgname):]
                            elif bldg == 'ABRD':
                                intendhsg = 'O'
                                room = bldgname[(bldgname.find('_') + 1)
                                                - len(bldgname):]
                            elif bldg == 'UN':
                                intendhsg = 'O'
                                room = bldgname[(bldgname.find('_') + 1)
                                                - len(bldgname):]
                            else:
                                intendhsg = 'R'
                                room = i[4]

                            # Use cancelation reason
                            if cancelreason == 'Withdrawal':
                                rsvstat = 'W'
                                billcode = 'NOCH'
                            else:
                                rsvstat = 'R'

                            # This may be useful to determine which records
                            # have been pulled and processed
                            print("ROOMASSIGNMENTID = "
                                  + str(roomassignmentid))

                            csvWriter = csv.writer(room_output,
                                                   quoting=csv.QUOTE_NONNUMERIC
                                                   )
                            # csvWriter.writerow(i)
                            # Need to write translated fields if csv is to
                            # be created
                            csvWriter.writerow([carthid, bldgname, bldg,
                                                floor, room, bed, room_type,
                                                occupancy, roomusage,
                                                timeframenumericcode, checkin,
                                                checkedindate, checkout,
                                                checkedoutdate, po_box,
                                                po_box_combo, canceled,
                                                canceldate, cancelnote,
                                                cancelreason, ghost, posted,
                                                roomassignmentid])
                            # print(str(carthid) + ', ' + str(billcode) + ', '
                            #       + str(bldg) + ', ' + str(room) + ', ' +
                            #       + str(room_type))
                            # Validate if the stu_serv_rec exists first
                            # update stu_serv_rec id, sess, yr, rxv_stat,
                            # intend_hsg, campus, bldg, room, bill_code
                            q_validate_stuserv_rec = '''
                                          select id, sess, yr, rsv_stat, 
                                          intend_hsg, campus, bldg, room, 
                                          no_per_room, 
                                          add_date, 
                                          bill_code, hous_wd_date 
                                          from stu_serv_rec 
                                          where yr = {2}
                                          and sess  = "{1}"
                                          and id = {0}'''.format(carthid,
                                                                 sess, year)
                            # print(q_validate_stuserv_rec)

                            # ret = do_sql(q_validate_stuserv_rec, earl=EARL)
                            ret = do_sql(q_validate_stuserv_rec, key=DEBUG,
                                         earl=EARL)

                            if ret is not None:
                                if billcode > 0:
                                    # compare rsv_stat, intend_hsg, bldg, room,
                                    # billcode
                                    # Update only if something has changed
                                    print("Record found " + carthid)

                                    row = ret.fetchone()
                                    if row is not None:
                                        print(row[3] + "," + str(rsvstat))
                                        print(row[4] + "," + str(intendhsg))
                                        print(row[6] + "," + str(bldg))
                                        print(row[7] + "," + str(room))
                                        print(row[10] + "," + str(billcode))
                                        if row[3] != rsvstat \
                                                or row[4] != intendhsg \
                                                or row[6] != bldg \
                                                or row[7] != room \
                                                or row[10] != billcode:
                                            print("Need to update "
                                                  "stu_serv_rec")
                                            q_update_stuserv_rec = '''
                                            UPDATE stu_serv_rec set  
                                            rsv_stat = ?,
                                            intend_hsg = ?, campus = ?, 
                                            bldg = 
                                            ?, room = ?,
                                            no_per_room = ?, add_date = ?, 
                                            bill_code = ?,
                                            hous_wd_date = ?
                                            where id = ? and sess = ? and 
                                            yr = ?'''
                                            q_update_stuserv_args = (rsvstat,
                                                intendhsg,
                                                "MAIN", bldg,
                                                room,
                                                occupants,
                                                checkedindate,
                                                billcode,
                                                checkedoutdate,
                                                carthid,
                                                sess, year)
                                            print(q_update_stuserv_rec)
                                            print(q_update_stuserv_args)
                                            engine.execute(
                                                q_update_stuserv_rec,
                                                q_update_stuserv_args)

                                            fn_mark_posted(carthid, room,
                                                           adir_hallcode, term)

                                        else:
                                            print("No change needed in "
                                                  "stu_serv_rec")
                                            fn_mark_posted(carthid, room,
                                                           adir_hallcode, term)

                                    else:
                                        print("fetch retuned none - No "
                                              "stu_serv_rec for student "
                                              + carthid + " for term " + term)

                                else:
                                    print("Bill code not found")
                            #     # go ahead and update
                            else:
                                print("Record not found")

                                body = "Student Service Record does not " \
                                       "exist. Please inquire why."
                                subj = "Adirondack - Stu_serv_rec missing"
                                sendmail("dsullivan@carthage.edu",
                                         "dsullivan@carthage.edu", body, subj)

                                # Insert if no record exists, update else
                                # Dave says stu_serv_rec should NOT be created
                                # from Adirondack data.  Other offices need
                                # to create the initial record
                                # Need to send something to Marietta
                                # if billcode > 0:
                                #     q_insert_stuserv_rec = '''
                                #             INSERT INTO stu_serv_rec (id,
                                #             sess, yr, rsv_stat, intend_hsg,
                                #             campus, bldg, room, no_per_room,
                                #             add_date,bill_code, hous_wd_date)
                                #             VALUES (?,?,?,?,?,?,?,?,?,?,?)'''
                                #     q_insert_stuserv_args = (
                                #         carthid, term, yr, rsvstat, 'R',
                                #         'MAIN', bldg, room, occupants,
                                #         checkedindate, billcode,
                                #         checkedoutdate)
                                #     print(q_insert_stuserv_rec)
                                #     print(q_insert_stuserv_args)
                                #     # engine.execute(q_insert_stuserv_rec,
                                #     # q_insert_stuserv_args)

                                # else:
                                #     print("Bill code not found")

                # filepath = settings.ADIRONDACK_CSV_OUTPUT

    except Exception as e:
        print(
                "Error in adirondack_room_assignments_api.py- Main:  " +
                e.message)
        # fn_write_error("Error in adirondack_std_billing_api.py - Main: "
        #                + e.message)


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test
    database = args.database

    if not database:
        print "mandatory option missing: database name\n"
        parser.print_help()
        exit(-1)
    else:
        database = database.lower()

    if database != 'cars' and database != 'train' and database != 'sandbox':
        print "database must be: 'cars' or 'train' or 'sandbox'\n"
        parser.print_help()
        exit(-1)

    sys.exit(main())

