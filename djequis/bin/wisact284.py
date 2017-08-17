import os
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import timedelta
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

#from djequis.sql.wisact284 import WIS_ACT_284_SQL
from djequis.sql.wisact284 import getaid
from djequis.sql.wisact284 import getaidcount
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Wisconsin ACT 284
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--dispersed",
    action='store_true',
    help="amount status = AD",
    dest="dispersed"
)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    # set date and time to be added to the filename
    datetimestr = time.strftime("%Y%m%d")

    # Looks at queries and determines if aid has been despersed
    if dispersed:
        getaid_sql = getaid(True)
        #print (getaid_sql)
        getcount_sql = getaidcount(True)
        #print (getcount_sql)
    else:
        getaid_sql = getaid(False)
        #print (getaid_sql)
        getcount_sql = getaidcount(False)
        #print (getcount_sql)

    # run SQL statement
    sqlresults = do_sql(getaid_sql, earl=EARL)
    # if there are no results

    if sqlresults is None:
        print ("Funds have not been dispersed.")
        # send email
        SUBJECT = '[Wisconsin Act 284]'
        BODY = 'Funds have not been dispersed.\n\n'
        sendmail(
            settings.WISACT_TO_EMAIL,settings.WISACT_FROM_EMAIL,
            SUBJECT, BODY
        )
    else:
        # run SQL statement
        sqlcountresults = do_sql(getcount_sql, earl=EARL)
        # gets the first record 
        maxaidcount = (sqlcountresults.fetchone()["number_of_loans"]) # fetch the max loan number
        print ('Highest Number of loans: {0}'.format(maxaidcount)) # fetch the first row only
        # set directory and filename to be stored
        filename=('{0}CCM-{1}.csv'.format(
            settings.WISACT_CSV_OUTPUT,datetimestr
        ))
        phile = open(filename,"w");
        writer = csv.writer(phile)
        # creates non-dynamic part of the header
        csv_line = ["School OPEID", "Academic Year", "Student SSN", "Student First Name",
                    "Student Last Name", "School Student ID", "Student Address Line 1",
                    "student Address Line 2", "Student Address Line 3", "Student City",
                    "Student State", "Student Zip", "Student Country", "Student Email",
                    "Tuition", "Room & Board", "Books & Supplies", "Transportation",
                    "Other Education Costs", "Loan Fees"
                    ]
        for aidindex in range (1, maxaidcount):
            csv_line.extend(('Private Loan Code'+ ' ' +str(aidindex), 'Private Loan Name'+ ' ' +str(aidindex),
                        'Private Loan Amount'+ ' ' +str(aidindex), 'Institutional Grants'+ ' ' +str(aidindex),
                        'Institutional Scholarship'+ ' ' +str(aidindex), 'Federal Grants'+ ' ' +str(aidindex),
                        'State Grants'+ ' ' +str(aidindex), 'Outside Aid'+ ' ' +str(aidindex),
                        'Loan Date'+ ' ' +str(aidindex)))
        print (csv_line)
        # set currentID 0
        currentID = 0
        for row in sqlresults:
            if row["student_id_number"] != currentID:
                print (csv_line)
                # creates header in .csv
                writer.writerow(csv_line)
                currentID = row["student_id_number"]
                # creates non-dynamic data of student record
                csv_line = (row["opeid"], row["acadyear"], row["social_security_number"],
                        row["student_first_name"], row["student_last_name"],
                        row["student_id_number"], row["student_address_line_1"],
                        row["student_address_line_2"], row["student_address_line_3"],
                        row["student_city"], row["student_state_code"],
                        row["student_postal_code"], row["student_country_code"],
                        row["student_email"], row["c_tufe"], row["c_rmbd"],
                        row["c_book"], row["c_tran"], row["c_misc"],
                        row["c_loan"])
                print ('Current ID: {0}'.format(currentID))
                # adds each financial aid record to row for student
            csv_line += (row["aid_code"], row["loan_name"], "% .2f" % row["aid_amount"],
                          "% .2f" % row["c_instgrants"], "% .2f" % row["c_instscholar"],
                          "% .2f" % row["c_fedgrants"], "% .2f" % row["c_stegrants"],
                          "% .2f" % row["c_outsideaid"], row["loan_date"])
        print (csv_line)
        writer.writerow(csv_line)

        phile.close()

if __name__ == "__main__":
    args = parser.parse_args()
    dispersed = args.dispersed
    test = args.test

    sys.exit(main())