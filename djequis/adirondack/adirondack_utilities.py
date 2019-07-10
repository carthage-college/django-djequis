import csv
import datetime
from datetime import datetime
from datetime import date
import codecs
import time
from time import strftime, strptime

# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
# from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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


def fn_convert_date(date):
    # print(date)
    if date != "":
        ndate = datetime.strptime(date, "%Y-%m-%d")
        retdate = datetime.strftime(ndate, "%m/%d/%Y")
    else:
        retdate = ''
    # print(str(date) + ',' + str(retdate))
    return retdate



def fn_write_misc_header():
    print("Write Header")
    with codecs.open(settings.ADIRONDACK_ROOM_DAMAGES, 'wb',
                     encoding='utf-8-sig') as fee_output:

    # with open('ascii_room_damages.csv', 'wb') as fee_output:
        csvWriter = csv.writer(fee_output)
        csvWriter.writerow(["ITEM_DATE","BILL_DESCRIPTION","ACCOUNT_NUMBER",
                            "AMOUNT","STUDENT_ID","TOT_CODE","BILL_CODE",
                            "TERM"])


def fn_write_billing_header():
    print("Write Header")
    with open(settings.ADIRONDACK_ROOM_FEES, 'wb') as room_output:
        csvWriter = csv.writer(room_output)
        csvWriter.writerow(["STUDENTNUMBER","ITEMDATE","AMOUNT","TIMEFRAME",
                            "TIMEFRAMENUMERICCODE","BILLDESCRIPTION",
                            "ACCOUNT","ACCOUNT_DISPLAY_NAME","EFFECTIVEDATE",
                            "EXPORTED","EXPORTTIMESTAMP","BILLEXPORTDATE",
                            "TERMEXPORTSTARTDATE","ITEMTYPE","ASSIGNMENTID",
                            "DININGPLANID","STUDENTBILLINGINTERNALID",
                            "USERNAME","ADDITIONALID1"])


def fn_write_assignment_header():
    print("Write Header")
    with open(settings.ADIRONDACK_ROOM_ASSIGNMENTS, 'wb') as room_output:
        csvWriter = csv.writer(room_output)
        csvWriter.writerow(["STUDENTNUMBER","HALLNAME","HALLCODE","FLOOR",
        "ROOMNUMBER","BED","ROOM_TYPE","OCCUPANCY","ROOMUSAGE",
        "TIMEFRAMENUMERICCODE","CHECKIN","CHECKEDINDATE","CHECKOUT",
        "CHECKEDOUTDATE","PO_BOX","PO_BOX_COMBO","CANCELED","CANCELDATE",
        "CANCELNOTE","CANCELREASON","GHOST","POSTED","ROOMASSIGNMENTID"])

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
    return("Error logged")


def sendmail(to, frum, body, subject, debug=False):
    # Create the message
    msg = MIMEMultipart('alternative')
    msg['To'] = to
    msg['From'] = frum
    msg['Subject'] = subject
    # Open the files in binary mode.  Let the MIMEImage class automatically
    # guess the specific image type.

    # maintype, subtype = ctype.split("/", 1)

    fp = open(settings.ADIRONDACK_ROOM_DAMAGES,  'rb')
    # attachment = MIMEText(fp.read(), _subtype=subtype)
    attachment = MIMEText(fp.read())
    # print(str(attachment))
    # txt = MIMEText(fp.read())
    fp.close()
    msg.attach(str(attachment))

    print("ready to send")

    server = smtplib.SMTP('localhost')
    # show communication with the server
    # if debug:
    #     server.set_debuglevel(True)
    try:
        print(frum)
        # print(to)
        # print(msg)
        # print(msg.as_string())
        server.sendmail(frum, to, msg.as_string())

    finally:
        print("Done")
    #     server.quit()



def fn_write_log(msg):
    # create console handler and set level to info
    # handler = logging.FileHandler(
    #     '{0}apdtocx.log'.format(settings.LOG_FILEPATH))
    # handler.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(
    # message)s',
    #                               datefmt='%m/%d/%Y %I:%M:%S %p')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)
    # logger.info(msg)
    # handler.close()
    # logger.removeHandler(handler)
    # info_logger = logging.getLogger('info_logger')
    # info_logger.info(msg)
    # fn_clear_logger()
    return("Message logged")

def fn_clear_logger():
    logging.shutdown()
    return("Clear Logger")


# def sample_function(secret_parameter):
#     logger = logging.getLogger(__name__)  # __name__=projectA.moduleB
#     logger.debug("Going to perform magic with '%s'",  secret_parameter)
#
#     try:
#         result = print(secret_parameter)
#     except IndexError:
#         logger.exception("OMG it happened again, someone please tell Laszlo")
#     except:
#         logger.info("Unexpected exception", exc_info=True)
#         raise
#     else:
#         logger.info("Magic with '%s' resulted in '%s'", secret_parameter, result, stack_info=True)