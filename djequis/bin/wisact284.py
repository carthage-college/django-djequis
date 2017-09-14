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

from djequis.sql.wisact284 import getaid
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL
DEBUG = settings.INFORMIX_DEBUG

################################################################################
# The objective of the School College Cost Meter (CCM) File is to help schools
# provide detailed student information to Great Lakes in a standard format that
# correctly populates the College Cost Meter.
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
    headerdate = time.strftime("%Y%m%d")
    datetimestr = time.strftime("%Y%m%d%H%M%S")

    # Looks at query and determines if aid has been despersed
    getaid_sql = getaid(dispersed)

    # run getaid_sql SQL statement
    sqlresults = do_sql(getaid_sql, key=DEBUG, earl=EARL)
    # if there are no results sned email
    if sqlresults is None:
        # send email
        SUBJECT = '[Wisconsin Act 284]'
        BODY = 'Funds have not been dispersed.\n\n'
        sendmail(
            settings.WISACT_TO_EMAIL,settings.WISACT_FROM_EMAIL,
            BODY, SUBJECT
        )
    else:
        # set directory and filename where to be stored
        filename=('{0}CCM-{1}.csv'.format(
            settings.WISACT_CSV_OUTPUT,datetimestr
        ))
        phile = open(filename,"w");
        writer = csv.writer(phile)
        # if command line --test then header will be printed
        if test:
            header = ["File Name", "School OPEID", "File Date"]
            # writes file header
            writer.writerow(header)
        # displays file header elements
        header_detail = ("CCM", "00383900", headerdate)
        # writes file header elements
        writer.writerow(header_detail)
        # if command line --test then loan header will be printed
        if test:
            loan_header = ["School OPEID", "Academic Year", "Student SSN",
                "Student First Name", "Student Last Name", "School Student ID",
                "Student Address Line 1", "Student Address Line 2",
                "Student Address Line 3", "Student City", "Student State",
                "Student Zip", "Student Country", "Student Email Address",
                "Private Loan Name 1", "Private Loan Amount 1", "Repayment Length",
                "Private Loan Interest Rate", "Loan Date 1", "Private Loan Name 2",
                "Private Loan Amount 2", "Repayment Length", "Private Loan Interest Rate",
                "Loan Date 2", "Private Loan Name 3", "Private Loan Amount 3",
                "Repayment Length", "Private Loan Interest Rate", "Loan Date 3",
                "Private Loan Name 4", "Private Loan Amount 4", "Repayment Length",
                "Private Loan Interest Rate", "Loan Date 4", "Private Loan Name 5",
                "Private Loan Amount 5", "Repayment Length", "Private Loan Interest Rate",
                "Loan Date 5", "Private Loan Name 6", "Private Loan Amount 6",
                "Repayment Length", "Private Loan Interest Rate", "Loan Date 6",
                "Institutional Loan Name 1", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "Institutional Loan Name 2", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "Institutional Loan Name 3", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "Institutional Loan Name 4", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "Institutional Loan Name 5", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "Institutional Loan Name 6", "Institutional Loan Amount",
                "Institutional Loan Interest Rate", "Repayment Length", "Loan Date",
                "State Loan Name 1", "State Loan Amount", "State Loan Interest Rate",
                "Repayment Length", "Loan Date", "State Loan Name 2",
                "State Loan Amount", "State Loan Interest Rate", "Repayment Length",
                "Loan Date", "State Loan Name 3", "State Loan Amount",
                "State Loan Interest Rate", "Repayment Length", "Loan Date",
                "State Loan Name 4", "State Loan Amount", "State Loan Interest Rate",
                "Repayment Length", "Loan Date", "State Loan Name 5",
                "State Loan Amount", "State Loan Interest Rate", "Repayment Length",
                "Loan Date", "State Loan Name 6", "State Loan Amount",
                "State Loan Interest Rate", "Repayment Length", "Loan Date",
                "Tuition", "Tuition Fees", "Room & Board", "Books & Supplies",
                "Transportation", "Other Education Costs", "Personal Education Costs",
                "Loan Fees", "Institutional Grants", "Institutional Scholarship",
                "Federal Grants", "State Grants", "Other Scholarships"
                ]
            # writes loan header elements
            writer.writerow(loan_header)
        #######################################################################
        # loops through maxaidcount to dynamically add file detail header for
        # loans. It will add as many extra loans as found in the max aid count
        #######################################################################
        currentID = 0 # initializing currentID 0
        loanCount = 0 # initializing loanCount 0
        maxaidcount = 18 # set maxaid count
        for row in sqlresults:
            if row["student_id_number"] != currentID:
                if currentID != 0:
                    # loops through maxaidcount to add private loans
                    for i in range (loanCount, maxaidcount):
                        # creates spacing in between private loan data other loan information
                        csv_line += ("", "", "", "", "")
                    # adds other loan information
                    csv_line += (row["c_tufe"], "", row["c_rmbd"],
                        row["c_book"], row["c_tran"], row["c_misc"], "", row["c_loan"],
                        "% .2f" % row["c_instgrants"], "% .2f" % row["c_instscholar"],
                        "% .2f" % row["c_fedgrants"], "% .2f" % row["c_stegrants"],
                        "% .2f" % row["c_outsideaid"])
                    writer.writerow(csv_line)
                currentID = row["student_id_number"]
                loanCount = 0
                ###############################################################
                # writes non-dynamic detail file data of the student record
                # adds each financial aid loan record to same row for student
                # The % .2f is to keep the decimal format
                 ##############################################################
                csv_line = (row["opeid"], row["acadyear"], row["social_security_number"],
                    row["student_first_name"], row["student_last_name"],
                    row["student_id_number"], row["student_address_line_1"],
                    row["student_address_line_2"], row["student_address_line_3"],
                    row["student_city"], row["student_state_code"],
                    row["student_postal_code"], row["student_country_code"],
                    row["student_email"])
            csv_line += (row["loan_name"], "% .2f" % row["aid_amount"], "", "",
                        row["loan_date"])
            loanCount = loanCount +1
        # writes the last line for the last student loan record
        writer.writerow(csv_line)
    # closes file
    phile.close()

if __name__ == "__main__":
    args = parser.parse_args()
    dispersed = args.dispersed
    test = args.test

    sys.exit(main())