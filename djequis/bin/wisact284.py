import os
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import timedelta
import time
import argparse
from decimal import Decimal

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
DEBUG = settings.INFORMIX_DEBUG

################################################################################
# The objective of the School College Cost Meter File is to help schools provide
# detailed student information to Great Lakes in a standard format that correctly
# populates the College Cost Meter.
#
# The School College Cost Meter File will list all students to which Great Lakes
# will send an email or letter detailing required state law information.
###############################################################################
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
    # set date and time to be added to the filename string
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Looks at queries and determines if aid has been despersed
    if dispersed:
        getaid_sql = getaid(True)
        getcount_sql = getaidcount(True)
    else:
        getaid_sql = getaid(False)
        getcount_sql = getaidcount(False)

    # run getaid_sql SQL statement
    sqlresults = do_sql(getaid_sql, key=DEBUG, earl=EARL)
    # if there are no results sned email
    if sqlresults is None:
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
        # fetch the first row and get max loan number from the number of loans column
        maxaidcount = (sqlcountresults.fetchone()["number_of_loans"]) 
        # if command line --test prints out number of loans
        if test:
            print ('Highest Number of loans: {0}'.format(maxaidcount))
        # set directory and filename to be stored
        filename=('{0}CCM-{1}.csv'.format(
            settings.WISACT_CSV_OUTPUT,datetimestr
        ))
        phile = open(filename,"w");
        writer = csv.writer(phile)
        # sets non-dynamic file header
        header = ["File Name", "School OPEID", "File Date"]
        # writes file header
        writer.writerow(header)
        # sets file header elements
        header_detail = ("CCM", "00383900", datetimestr)
        # writes file header elements
        writer.writerow(header_detail)
        #######################################################################
        # sets non-dynamic part of the file detail header
        # Institutional Loan, State Loan not captured but placeholder needs to
        # be provided
        #######################################################################
        csv_line = ["School OPEID", "Academic Year", "Student SSN", "Student First Name",
            "Student Last Name", "School Student ID", "Student Address Line 1",
            "Student Address Line 2", "Student Address Line 3", "Student City",
            "Student State", "Student Zip", "Student Country", "Student Email Address",
            "Tuition", "Room & Board", "Books & Supplies", "Transportation",
            "Other Education Costs", "Loan Fees", "Institutional Grants",
            "Institutional Scholarship", "Federal Grants", "State Grants",
            "Outside Aid", "Institutional Loan", "Institutional Loan Amount",
            "Institutional Loan Interest Rate", "Repayment Length",
            "State Loan", "State Loan Amount", "State Loan Interest Rate",
            "Repayment Length"
            ]
        #######################################################################
        # loops through maxaidcount to dynamically add file detail header for loans.
        # It will add as many extra loans as found in the max aid count
        #######################################################################
        for aidindex in range (1, maxaidcount+1):
            csv_line.extend(('Private Loan Name'+ ' ' +str(aidindex),
            'Private Loan Amount'+ ' ' +str(aidindex), 'Repayment Length',
            'Private Loan Interest Rate', 'Loan Date'+ ' ' +str(aidindex)))
        # if command line --test prints out csv_line
        if test:
            print (csv_line)
        # initializing currentID 0
        currentID = 0
        for row in sqlresults:
            if row["student_id_number"] != currentID:
                # if command line --test prints out csv_line
                if test:
                    print (csv_line)
                # writes file detail header
                writer.writerow(csv_line)
                currentID = row["student_id_number"]
                # writes non-dynamic detail file data of the student record
                csv_line = (row["opeid"], row["acadyear"], row["social_security_number"],
                    row["student_first_name"], row["student_last_name"],
                    row["student_id_number"], row["student_address_line_1"],
                    row["student_address_line_2"], row["student_address_line_3"],
                    row["student_city"], row["student_state_code"],
                    row["student_postal_code"], row["student_country_code"],
                    row["student_email"], row["c_tufe"], row["c_rmbd"],
                    row["c_book"], row["c_tran"], row["c_misc"],
                    row["c_loan"], "% .2f" % row["c_instgrants"],
                    "% .2f" % row["c_instscholar"], "% .2f" % row["c_fedgrants"],
                    "% .2f" % row["c_stegrants"], "% .2f" % row["c_outsideaid"],
                    "", "", "", "", "", "", "", "")
                # if command line --test prints out student ID
                if test:
                    print ('Current ID: {0}'.format(currentID))
                #######################################################################
                # adds each financial aid loan record to row for student
                # to the backend of the file. The % .2f is to keep the decimal format
                 #######################################################################
            csv_line += (row["loan_name"], "% .2f" % row["aid_amount"], "", "",
                         row["loan_date"])
        # if command line --test prints out csv_line
        if test:
            print (csv_line)
        # writes the last line for the last student loan record
        writer.writerow(csv_line)
        # closes file
        phile.close()

if __name__ == "__main__":
    args = parser.parse_args()
    dispersed = args.dispersed
    test = args.test

    sys.exit(main())