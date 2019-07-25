import csv
import datetime
import calendar
from datetime import date
import codecs
import time
import hashlib
from time import strftime, strptime
# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
# from email.mime.image import MIMEImage
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# import argparse
import logging
from logging.handlers import SMTPHandler

# django settings for script
from django.conf import settings

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
    with codecs.open(settings.ADIRONDACK_ROOM_DAMAGES, 'wb',
                     encoding='utf-8-sig') as fee_output:
        # with open('ascii_room_damages.csv', 'wb') as fee_output:
        csvWriter = csv.writer(fee_output)
        csvWriter.writerow(["ITEM_DATE", "BILL_DESCRIPTION", "ACCOUNT_NUMBER",
                            "AMOUNT", "STUDENT_ID", "TOT_CODE", "BILL_CODE",
                            "TERM"])


def fn_write_billing_header():
    with open(settings.ADIRONDACK_ROOM_FEES, 'wb') as room_output:
        csvWriter = csv.writer(room_output)
        csvWriter.writerow(["STUDENTNUMBER", "ITEMDATE", "AMOUNT", "TIMEFRAME",
                            "TIMEFRAMENUMERICCODE", "BILLDESCRIPTION",
                            "ACCOUNT", "ACCOUNT_DISPLAY_NAME", "EFFECTIVEDATE",
                            "EXPORTED", "EXPORTTIMESTAMP", "BILLEXPORTDATE",
                            "TERMEXPORTSTARTDATE", "ITEMTYPE", "ASSIGNMENTID",
                            "DININGPLANID", "STUDENTBILLINGINTERNALID",
                            "USERNAME", " ADDITIONALID1"])


def fn_write_assignment_header():
    with open(settings.ADIRONDACK_ROOM_ASSIGNMENTS, 'wb') as room_output:
        csvWriter = csv.writer(room_output)
        csvWriter.writerow(["STUDENTNUMBER", "HALLNAME", "HALLCODE", "FLOOR",
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
        csvWriter = csv.writer(output)
        csvWriter.writerow(["STUDENTNUMBER", "APPLICATIONTYPENAME",
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
        # with open("carthage_students.txt", 'w') as file_out:
        csvWriter = csv.writer(file_out, delimiter='|')
        csvWriter.writerow(
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
             "CONTACT3_COUNTRY", "TERM", "RACECODE"])
    file_out.close()


#########################################################
# Common functions to handle logger messages and errors
#########################################################

def fn_write_error(msg):
    # create error file handler and set level to error
    handler = logging.FileHandler(
        '{0}cc_apd_rec_error.log'.format(settings.LOG_FILEPATH))
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

    msg.attach(MIMEText(body, 'csv'))
    filename = settings.ADIRONDACK_ROOM_DAMAGES
    # print(filename)
    attachment = open(settings.ADIRONDACK_ROOM_DAMAGES, 'rb')
    fil = MIMEBase('application', 'octet-stream')
    fil.set_payload(attachment.read())
    encoders.encode_base64(fil)
    fil.add_header('Content-Disposition',
                   "attachment; filename = %s" % filename)
    msg.attach(fil)
    # print("attach OK")
    text = msg.as_string()
    # print(text)
    # print("ready to send")
    server = smtplib.SMTP('localhost')
    # show communication with the server
    # if debug:
    #     server.set_debuglevel(True)
    try:
        print(msg['To'])
        print(msg['From'])
        server.sendmail(msg['From'], msg['to'], text)

        # server.sendmail(msg['From'], msg['To'], msg.as_string())

    finally:
        server.quit()
        # print("Done")
    #     server.quit()


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
