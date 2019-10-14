import os
import csv
import datetime
import json
import calendar
from datetime import date
import requests
import codecs
import time
import hashlib
from time import strftime, strptime
import smtplib
import mimetypes
import django

# ________________
# Note to self, keep this here
# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
django.setup()
# ________________
# django settings for script
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import logging
from logging.handlers import SMTPHandler
# from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Upload ADP data to CX
"""

# create logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def fn_get_bill_code(idnum, bldg, roomtype, roomassignmentid, session,
                     api_server, api_key):
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        hash_object = hashlib.md5(hashstring.encode())
        # print(session)
        # print(bldg)
        # print(idnum)
        # print(roomtype)
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            +api_server+"/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key=" + api_key + "&" + "utcts=" + \
            str(utcts) + "&" + "h=" + \
            hash_object.hexdigest() + "&" + \
            "ASSIGNMENTID=" + str(roomassignmentid) + "&" + \
            "EXPORTED=0,-1"
        # "TIMEFRAMENUMERICCODE=" + session


        # "ItemType=" + roomtype.strip() + "&" + \
        # __"STUDENTNUMBER=" + idnum + "&" + \
        #             _____________________________
        # Need to dynamically get the term - see the misc fee file
        # _______________________________
        # print(url)

        response = requests.get(url)
        x = json.loads(response.content)
        if not x['DATA']:
            # print("No data")
            if bldg == 'CMTR':
                billcode = 'CMTR'
            elif bldg == 'OFF':
                billcode = 'OFF'
            elif bldg == 'ABRD':
                billcode = 'ABRD'
            else:
                billcode = ''
            # print("Billcode found as " + billcode)
            return billcode
        else:
            for rows in x['DATA']:
                # print("ASSIGNMENTID = " + str(rows[14]))
                if roomassignmentid == rows[14]:
                    # print(rows[6])
                    billcode = rows[6]
                    # print("Billcode found as " + billcode)
                    return billcode
    except Exception as e:
        print(
                "Error in utilities.py- "
                "fn_get_bill_code:  " + e.message)
        fn_write_error("Error in utilities.py "
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


def fn_translate_bldg_for_adirondack(bldg_code):
    # Hall codes in Adirondack do not match CX, primarily OAKS
    # Allow both versions of the OAKS options
    switcher = {
        "OAK1": "OAKS1",
        "OAKS1": "OAKS1",
        "OAK2": "OAKS 2",
        "OAKS 2": "OAKS 2",
        "OAK3": "OAKS 3",
        "OAKS 3": "OAKS 3",
        "OAK4": "OAKS 4",
        "OAKS 4": "OAKS 4",
        "OAK5": "OAKS 5",
        "OAKS 5": "OAKS 5",
        "OAK6": "OAKS 6",
        "OAKS 6": "OAKS 6",
        "DEN": "DEN",
        "JOH": "JOH",
        "MADR": "MADR",
        "SWE": "SWE",
        "TAR": "TAR",
        "UN": "UN",
        "ABRD": "ABRD",
        "CMTR": "CMTR",
        "OFF": "OFF",
        "TOWR": "TOWR",
        "WD": "WD"
    }
    return switcher.get(bldg_code, "Invalid Building")


def fn_mark_room_posted(stu_id, room_no, hall_code, term, posted,
                        api_server, api_key):
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + settings.ADIRONDACK_API_SECRET
        hash_object = hashlib.md5(hashstring.encode())

        # print("In fn_mark_room_posted " + str(stu_id) + ", " + str(room_no)
        # + ", " + str(hall_code) + ", " + term)
        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            +api_server+"/apis/thd_api.cfc?" \
            "method=housingASSIGNMENTS&" \
            "Key=" + api_key + "&" \
            "utcts=" + \
            str(utcts) + "&" \
            "h=" + hash_object.hexdigest() + "&" \
            "TimeFrameNumericCode=" + term + "&" \
            "HallCode=" + hall_code + "&" \
            "Ghost=0" + "&" \
            "Posted=" + str(posted) + "&" \
            "RoomNumber=" + room_no + "&" \
            "STUDENTNUMBER=" + stu_id + "&" \
            "PostAssignments=-1"
        # "CurrentFuture=-1" + "&"
        # Room number won't work for off campus types - Room set to CMTR,
        # ABRD  etc. in CX.
        # + "&" \
        print(url)

        # DEFINITIONS
        # Posted: 0 returns only NEW unposted,
        #         1 returns posted, as in export out to our system
        #         2 changed or cancelled
        # PostAssignments: -1 will mark the record as posted.
        # CurrentFuture: -1 returns only current and future
        # Cancelled: -1 is for cancelled, 0 for not cancelled
        # Setting Ghost to -1 prevents rooms with no student from returning
        # print("URL = " + url)

        # response = requests.get(url)
        # x = json.loads(response.content)
        # if not x['DATA']:
        #     # print("Unable to mark record as posted - record not found")
        #     fn_write_error("Unable to mark record as posted - "
        #                    "record not found")
        # else:
        #     # print("Record marked as posted")
        #     pass

    except Exception as e:
        # print("Error in utilities.py- fn_mark_room_posted:  " +
        #       e.message)
        fn_write_error("Error in utilities.py- fn_mark_room_posted: "
                       + e.message)




def fn_mark_bill_exported(term, acct_code, bill_id, carthid,
                          api_server, api_key):
    try:
        utcts = fn_get_utcts()
        hashstring = str(utcts) + api_key
        hash_object = hashlib.md5(hashstring.encode())

        # print("term =  " + str(term))
        # print("acct_code id = " + str(acct_code))
        # print("carthid = " + str(carthid))
        # print("api_server = " + str(api_server))

        url = "https://carthage.datacenter.adirondacksolutions.com/" \
            + api_server + "/apis/thd_api.cfc?" \
            "method=studentBILLING&" \
            "Key=" + api_key + "&" \
            "utcts=" + str(utcts) + "&" \
            "h=" + hash_object.hexdigest() + "&" \
            "TIMEFRAMENUMERICCODE=" + term + "&" \
            "AccountCode=" + acct_code + "&" \
            "STUDENTBILLINGINTERNALID=" + bill_id + "&" \
            "Exported=0" + "&" \
            "EXPORTCHARGES=-1"
        # API Does not accept student ID as param if bill internal ID is used
        # print("URL = " + url)

        response = requests.get(url)
        x = json.loads(response.content)
        # print(x)
        if not x['DATA']:
            print("Unable to mark bill as exported - record not found")
        else:
            print("Bill marked as exported")

    except Exception as e:
        print("Error in utilities.py- fn_mark_room_posted:  " +
              e.message)
        # fn_write_error("Error in utilities.py- fn_mark_room_posted:
        # " + e.message)


def fn_convert_date(ddate):
    # print(date)
    if ddate != "":
        ndate = datetime.strptime(ddate, "%Y-%m-%d")
        retdate = datetime.strftime(ndate, "%m/%d/%Y")
    else:
        retdate = ''
    # print(str(date) + ',' + str(retdate))
    return retdate


def fn_write_misc_header():
    # with codecs.open(settings.ADIRONDACK_ROOM_FEES, 'wb',
    #                  encoding='utf-8-sig') as fee_output:
    with codecs.open(settings.ADIRONDACK_ROOM_FEES, 'wb') as fee_output:
        csvwriter = csv.writer(fee_output)
        csvwriter.writerow(["ITEM_DATE", "BILL_DESCRIPTION", "ACCOUNT_NUMBER",
                            "AMOUNT", "STUDENT_ID", "TOT_CODE", "BILL_CODE",
                            "TERM"])


def fn_write_billing_header(file_name):
    with open(file_name, 'wb') as room_output:
        csvwriter = csv.writer(room_output)
        csvwriter.writerow(["STUDENTNUMBER", "ITEMDATE", "AMOUNT", "TIMEFRAME",
                            "TIMEFRAMENUMERICCODE", "BILLDESCRIPTION",
                            "ACCOUNT", "ACCOUNT_DISPLAY_NAME", "EFFECTIVEDATE",
                            "EXPORTED", "EXPORTTIMESTAMP", "BILLEXPORTDATE",
                            "TERMEXPORTSTARTDATE", "ITEMTYPE", "ASSIGNMENTID",
                            "DININGPLANID", "STUDENTBILLINGINTERNALID",
                            "USERNAME", " ADDITIONALID1"])


def fn_write_assignment_header(file_name):
    with open(file_name, 'wb') as room_output:
        csvwriter = csv.writer(room_output)
        csvwriter.writerow(["STUDENTNUMBER", "HALLNAME", "HALLCODE", "FLOOR",
                            "ROOMNUMBER", "BED", "ROOM_TYPE", "OCCUPANCY",
                            "ROOMUSAGE",
                            "TIMEFRAMENUMERICCODE", "CHECKIN", "CHECKEDINDATE",
                            "CHECKOUT",
                            "CHECKEDOUTDATE", "PO_BOX", "PO_BOX_COMBO",
                            "CANCELED", "CANCELDATE",
                            "CANCELNOTE", "CANCELREASON", "GHOST", "POSTED",
                            "ROOMASSIGNMENTID"])


def fn_write_application_header():
    with open(settings.ADIRONDACK_APPLICATONS, 'wb') as output:
        csvwriter = csv.writer(output)
        csvwriter.writerow(["STUDENTNUMBER", "APPLICATIONTYPENAME",
                            "APP_RECEIVED", "APP_COMPLETE",
                            "TIMEFRAMENUMERICCODE", "ELECTRONIC_SIG_TS",
                            "CONTRACT_RECEIVED", "APP_CANCELED", "DEPOSIT",
                            "DEPOSIT_AMOUNT", "DEPOSIT_RECEIVED",
                            "PAYVENDORCONFIRMATION", "UNDERAGE",
                            "UNDERAGE_ELECTRONIC_SIG_TS", "INSURANCE_INTENT"
                            ])


def fn_write_student_bio_header():
    adirondackdata = ('{0}carthage_students.txt'.format(
        settings.ADIRONDACK_TXT_OUTPUT))

    with open(adirondackdata, 'w') as file_out:
        csvwriter = csv.writer(file_out, delimiter='|')
        csvwriter.writerow(
            ["STUDENT_NUMBER", "FIRST_NAME", "MIDDLE_NAME",
             "LAST_NAME", "DATE_OF_BIRTH", "GENDER",
             "IDENTIFIED_GENDER", "PREFERRED_NAME",
             "PERSON_TYPE", "PRIVACY_INDICATOR", "ADDITIONAL_ID1",
             "ADDITIONAL_ID2",
             "CLASS_STATUS", "STUDENT_STATUS", "CLASS_YEAR", "MAJOR",
             "CREDITS_SEMESTER",
             "CREDITS_CUMULATIVE", "GPA", "MOBILE_PHONE",
             "MOBILE_PHONE_CARRIER", "OPT_OUT_OF_TEXT",
             "CAMPUS_EMAIL", "PERSONAL_EMAIL", "PHOTO_FILE_NAME",
             "PERM_PO_BOX",
             "PERM_PO_BOX_COMBO", "ADMIT_TERM", "STUDENT_ATHLETE",
             "ETHNICITY", "ADDRESS1_TYPE", "ADDRESS1_STREET_LINE_1",
             "ADDRESS1_STREET_LINE_2", "ADDRESS1_STREET_LINE_3",
             "ADDRESS1_STREET_LINE_4", "ADDRESS1_CITY",
             "ADDRESS1_STATE_NAME", "ADDRESS1_ZIP", "ADDRESS1_COUNTRY",
             "ADDRESS1_PHONE",
             "ADDRESS2_TYPE", "ADDRESS2_STREET_LINE_1",
             "ADDRESS2_STREET_LINE_2", "ADDRESS2_STREET_LINE_3",
             "ADDRESS2_STREET_LINE_4", "ADDRESS2_CITY",
             "ADDRESS2_STATE_NAME", "ADDRESS2_ZIP", "ADDRESS2_COUNTRY",
             "ADDRESS2_PHONE",
             "ADDRESS3_TYPE", "ADDRESS3_STREET_LINE_1",
             "ADDRESS3_STREET_LINE_2", "ADDRESS3_STREET_LINE_3",
             "ADDRESS3_STREET_LINE_4", "ADDRESS3_CITY",
             "ADDRESS3_STATE_NAME", "ADDRESS3_ZIP", "ADDRESS3_COUNTRY",
             "ADDRESS3_PHONE",
             "CONTACT1_TYPE", "CONTACT1_NAME",
             "CONTACT1_RELATIONSHIP",
             "CONTACT1_HOME_PHONE",
             "CONTACT1_WORK_PHONE",
             "CONTACT1_MOBILE_PHONE",
             "CONTACT1_EMAIL",
             "CONTACT1_STREET",
             "CONTACT1_STREET2",
             "CONTACT1_CITY",
             "CONTACT1_STATE",
             "CONTACT1_ZIP",
             "CONTACT1_COUNTRY",
             "CONTACT2_TYPE", "CONTACT2_NAME",
             "CONTACT2_RELATIONSHIP", "CONTACT2_HOME_PHONE",
             "CONTACT2_WORK_PHONE", "CONTACT2_MOBILE_PHONE",
             "CONTACT2_EMAIL", "CONTACT2_STREET", "CONTACT2_STREET2",
             "CONTACT2_CITY", "CONTACT2_STATE", "CONTACT2_ZIP",
             "CONTACT2_COUNTRY", "CONTACT3_TYPE", "CONTACT3_NAME",
             "CONTACT3_RELATIONSHIP", "CONTACT3_HOME_PHONE",
             "CONTACT3_WORK_PHONE", "CONTACT3_MOBILE_PHONE",
             "CONTACT3_EMAIL", "CONTACT3_STREET", "CONTACT3_STREET2",
             "CONTACT3_CITY", "CONTACT3_STATE", "CONTACT3_ZIP",
             "CONTACT3_COUNTRY", "TERM", "RACECODE", "SPORT", "GREEK_LIFE"])
    file_out.close()


def fn_encode_rows_to_utf8(rows):
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




def fn_write_error(msg):
    # create error file handler and set level to error
    handler = logging.FileHandler(
        '{0}adirondack_error.log'.format(settings.LOG_FILEPATH))
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.error(msg)
    handler.close()
    logger.removeHandler(handler)
    fn_clear_logger()
    return "Error logged"


def fn_sendmailfees(to, frum, body, subject):
    # Create the message
    msg = MIMEMultipart()

    # email to addresses may come as list
    msg['To'] = ','.join(to)
    msg['From'] = frum
    msg['Subject'] = subject

    text = ''
    # This can be outside the file collection loop
    msg.attach(MIMEText(body, 'csv'))

    files = os.listdir(settings.ADIRONDACK_TXT_OUTPUT)
    # filenames = []
    for f in files:
        if f.find('misc_housing') != -1:
            # print(settings.ADIRONDACK_TXT_OUTPUT + f)
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(settings.ADIRONDACK_TXT_OUTPUT
                                  + f, "rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="%s"' % os.path.basename(f))
            msg.attach(part)
            text = msg.as_string()
            # print(text)

    # print("ready to send")
    server = smtplib.SMTP('localhost')
    # show communication with the server
    # if debug:
    #     server.set_debuglevel(True)
    try:
        # print(msg['To'])
        # print(msg['From'])
        server.sendmail(msg['From'], msg['to'], text)

    finally:
        # server.quit()
        # print("Done")
        pass

def fn_get_utcts():
    # GMT Zero hour is 1/1/70
    # Zero hour in seconds = 0
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
    return utcts


def fn_clear_logger():
    logging.shutdown()
    return "Clear Logger"
