import io
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

from djequis.sql.everbridge import STUDENT_UPLOAD
from djequis.sql.everbridge import ADULT_UPLOAD
from djequis.sql.everbridge import FACSTAFF_UPLOAD
from djequis.core.utils import sendmail
from djzbar.utils.informix import get_engine
from djzbar.settings import (
    INFORMIX_EARL_SANDBOX, INFORMIX_EARL_TEST, INFORMIX_EARL_PROD
)

# set up command-line options
desc = """
    Everbridge Upload
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "-t", "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
parser.add_argument(
    "-l", "--limit",
    help="Limit results to n",
    required=False,
    dest="limit"
)
parser.add_argument(
    "-d", "--database",
    help="database name.",
    dest="database"
)

# We currently send all records but future development may require that
# the script updates records

def main():

    # determines which database is being called from the command line
    if database == 'cars':
        EARL = INFORMIX_EARL_PROD
    elif database == 'train':
        EARL = INFORMIX_EARL_TEST
    elif database == 'sandbox':
        EARL = INFORMIX_EARL_SANDBOX
    else:
        # argument parser should have taken care of this scenario
        # and we will never arrive here.
        EARL = None

    engine = get_engine(EARL)

    # set dictionary
    dict = {
        'Student': STUDENT_UPLOAD,
        'Adult': ADULT_UPLOAD,
        'FacStaff': FACSTAFF_UPLOAD
    }

    # go to our storage directory on the server
    os.chdir(settings.EVERBRIDGE_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
       'host':settings.EVERBRIDGE_HOST,
       'username':settings.EVERBRIDGE_USER,
       'private_key':settings.EVERBRIDGE_PKEY,
       'cnopts':cnopts
    }
    for key, value in dict.iteritems():
        if limit:
            value += "LIMIT {}".format(limit)
        if test:
            print("key = {}, value = {}".format(key, value))

        badmatches = []
        sqlresult = engine.execute(value)

        if sqlresult:
            datetimestr = time.strftime("%Y%m%d%H%M%S")
            filename=('{}{}Upload-{}.csv'.format(
                settings.EVERBRIDGE_CSV_OUTPUT,key,datetimestr
            ))

            #phile=io.open(filename, 'w', newline='')
            phile=open(filename, 'wb')
            output=csv.writer(phile, dialect='excel', lineterminator='\n')

            if key == 'FacStaff': # write header row for FacStaff
                output.writerow([
                    "First Name","Middle Initial","Last Name","Suffix",
                    "External ID","Country","Business Name","Record Type",
                    "Phone 1","Phone Country 1","Phone 2","Phone Country 2",
                    "Email Address 1","Email Address 2","SMS 1","SMS 1 Country",
                    "Custom Field 1","Custom Value 1","Custom Field 2",
                    "Custom Value 2","Custom Field 3","Custom Value 3","END"
                ])
            else: # write header row for Student and Adult
                output.writerow([
                    "First Name","Middle Initial","Last Name","Suffix",
                    "External ID","Country","Business Name","Record Type",
                    "Phone 1","Phone Country 1","Email Address 1",
                    "Email Address 2","SMS 1","SMS 1 Country","Custom Field 1",
                    "Custom Value 1","Custom Field 2","Custom Value 2",
                    "Custom Field 3","Custom Value 3","END"
                ])
            for row in sqlresult:
                output.writerow(row)
                if test:
                    print("row = \n{}".format(row))
                # checking for Bad match in either Student or FacStaff query
                if row and ((row.customvalue1 and "Bad match:" in row.customvalue1)\
                or (row.customvalue2 and "Bad match:" in row.customvalue2)):
                    badmatches.append(
                        '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, '
                        '{10} {11} {12}, {13}, {14}, {15}, {16}, {17}, {18}, '
                        '{19} {20}\n\n'.format(
                            row.lastname, row.firstname, row.middleinitial,
                            row.suffix, row.externalid, row.country,
                            row.businessname, row.recordtype,
                            row.phone1, row.phonecountry1, row.emailaddress1,
                            row.emailaddress2, row.sms1, row.sms1country,
                            row.customfield1, row.customvalue1, row.customfield2,
                            row.customvalue2, row.customfield3, row.customvalue3,
                            row.end
                        )
                    )
                badmatches_table = ''.join(badmatches)
                if test:
                    print("badmatches = \n{}".format(badmatches))
            if badmatches:
                if test:
                    print("badmatches_table = \n{}".format(badmatches_table))
                    print("length of badmatches = {}.".format(len(badmatches)))
                SUBJECT = '[Everbridge] Bad match'
                BODY = '''
                    A bad match exists in the file we are sending to Everbridge.
                    \n\n{0}\n\n
                    Bad match records: {1}
                '''.format(badmatches_table, len(badmatches))
                sendmail(
                    settings.EVERBRIDGE_TO_EMAIL, settings.EVERBRIDGE_FROM_EMAIL,
                    BODY, SUBJECT
                )
            else:
                if test:
                    print('Do not send email')

            phile.close()

            if not test:
                # SFTP the CSV
                try:
                    print('sftp attempt')
                    print(filename)
                    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
                        sftp.chdir("replace/")
                        print("current working directory: {}".format(sftp.getcwd()))
                        sftp.put(filename, preserve_mtime=True)
                        print("file uploaded:")
                        for i in sftp.listdir():
                            print(i)
                            print(str(sftp.lstat(i)))
                        sftp.close()
                    print("sftp put success: {}".format(key))
                except Exception, e:
                    print('sftp put fail [{}]: {}'.format(key, e))
                    SUBJECT = '[Everbridge SFTP] {} failed'.format(key)
                    BODY = 'Unable to PUT upload to Everbridge server.\n\n{}'.format(
                        str(e)
                    )
                    sendmail(
                        settings.EVERBRIDGE_TO_EMAIL,settings.EVERBRIDGE_FROM_EMAIL,
                        SUBJECT, BODY
                    )

    print "Done"

if __name__ == "__main__":

    args = parser.parse_args()
    test = args.test
    limit = args.limit
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
