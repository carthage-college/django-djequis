import os
import sys
import pysftp
import csv
import time
import argparse

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

# django settings for script
from django.conf import settings

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from djequis.sql.orgsync import ORGSYNC_DATA
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    OrgSync Upload via sftp
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    """
    # go to our storage directory on the server
    os.chdir(settings.ORGSYNC_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    # sftp connection information
    XTRNL_CONNECTION = {
       'host':settings.ORGSYNC_HOST,
       'username':settings.ORGSYNC_USER,
       'private_key':settings.ORGSYNC_PKEY,
       'private_key_pass':settings.ORGSYNC_PASS,
       'cnopts':cnopts
    }
    """
    # run SQL statement
    sqlresult = do_sql(ORGSYNC_DATA, earl=EARL)
    if test:
        print (sqlresult)

    # set date and time string
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # set directory and filename
    filename='{}OrgSync-{}.csv'.format(settings.ORGSYNC_CSV_OUTPUT,datetimestr)

    # create file
    phile=open(filename,"w");
    output=csv.writer(phile, dialect='excel')

    # write header row to file
    output.writerow([
        "account.username", "account.new_username", "account.email_address",
        "account.first_name", "account.last_name", "account.middle_initial",
        "account.phone_number", "account.address", "account.city", "account.state",
        "account.zip", "account.country", "account.birthday", "identification_card_number",
        "portal", "group", "classification", "form_element.3172627// Gender",
        "form_element.3172629// Hometown", "form_element.3172630// Major 1",
        "form_element.3172630// Major 2", "form_element.3172630// Major 3",
        "form_element.3172631// Minor 1", "form_element.3172631// Minor 2",
        "form_element.3172631// Minor 3", "form_element.3172632// Student ID",
        "form_element.3172633// Ethnicity", "form_element.3172634// Projected Graduation Year",
        "form_element.3172635// Housing Status",
        "form_element.3172636// International Student",
        "form_element.3172637// Transfer Student", "form_element.3451747// Building",
        "form_element.3451748// Room Number", "form_element.3451749// Mailbox"
    ])
    # write data rows to file
    if sqlresult is not None:
        for row in sqlresult:
            if test:
                print (row)
            output.writerow(row)
    else:
        print ("No values in list")
    phile.close()
    """
    # sftp the file
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            sftp.chdir("incoming/")
            sftp.put(filename, preserve_mtime=True)
            sftp.close()
        if test:
            print "success: ORGSYNC UPLOAD"
    except Exception, e:
        if test:
            print e
        else:
            SUBJECT = '[OrgSync SFTP] ORGSYNC UPLOAD failed'
            BODY = 'Unable to PUT upload to OrgSync server.\n\n{}'.format(str(e))
            sendmail(
                settings.ORGSYNC_TO_EMAIL,settings.ORGSYNC_FROM_EMAIL,
                SUBJECT, BODY
            )
    """

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
