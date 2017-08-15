import os
import sys
import pysftp
import csv
import datetime
from datetime import date
from datetime import timedelta
import time
import argparse
import decimal

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

from djequis.sql.wisact284 import WIS_ACT_284_SQL
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Wisconsin ACT 284 Upload via sftp
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    #
    now_date = (date.today())
    print ('Now Date: {0}'.format(now_date))
    # set century and date string 
    datetimestr = time.strftime("%y%m%d")
    print (datetimestr)
    year = datetime.date.today().year
    print ('Year: {0}'.format(year))
    century = int(year/100)
    print ('Century: {0}'.format(century))
    decade = int(year%100)
    print ('Decade: {0}'.format(decade))
    print ('File Name: {0}{1}'.format(century,datetimestr))

    # run SQL statement
    sqlresults = do_sql(WIS_ACT_284_SQL, earl=EARL)
    #filename=('wisact284.csv')
    
    #phile = open(filename,"w");
    #writer = csv.writer(phile)
    #writer.writerow(('OPEID', 'StudentID', 'SSN', 'First Name', 'Last Name', 'Address Line 1', 'Address Line 2', 'Address Line 3', 'City', 'State', 'Zip', 'Country', 'Email', 'CTUFE', 'CRMBD', 'CBOOK', 'CTRAN', 'CMISC', 'CLOAN', 'ACADYR'))
    csv_line = ("OPEID", "StudentID", "SSN", "First Name", "Last Name",
                "Address Line 1", "Address Line 2", "Address Line 3", "City",
                "State", "Zip", "Country", "Email", "CTUFE", "CRMBD", "CBOOK",
                "CTRAN", "CMISC", "CLOAN", "ACADYR", "Aid Code 1", "Loan Name 1",
                "Aid Amount 1", "Instgrants 1", "Instscholar 1", "Fedgrants 1",
                "Stegrants 1", "Outside Aid 1", "Beginning Date 1", "Aid Code 2",
                "Loan Name 2", "Aid Amount 2", "Instgrants 2", "Instscholar 2",
                "Fedgrants 2", "Stegrants 2", "Outside Aid 2", "Beginning Date 2",
                "Aid Code 3", "Loan Name 3", "Aid Amount 3", "Instgrants 3",
                "Instscholar 3", "Fedgrants 3", "Stegrants 3", "Outside Aid 3",
                "Beginning Date 3", "Aid Code 4", "Loan Name 4", "Aid Amount 4",
                "Instgrants 4", "Instscholar 4", "Fedgrants 4", "Stegrants 4",
                "Outside Aid 4", "Beginning Date 4", "Aid Code 5", "Loan Name 5",
                "Aid Amount 5", "Instgrants 5", "Instscholar 5", "Fedgrants 5",
                "Stegrants 5", "Outside Aid 5", "Beginning Date 5", "Aid Code 6",
                "Loan Name 6", "Aid Amount 6", "Instgrants 6", "Instscholar 6",
                "Fedgrants 6", "Stegrants 6", "Outside Aid 6", "Beginning Date 6"
                )
    currentID = 0

    for row in sqlresults:
        if row["student_id_number"] != currentID:
            #print (row["student_id_number"])
            #print ('Write line to csv')
            print (csv_line)
            #writer.writerow(row["student_id_number"])
            currentID = row["student_id_number"]
            csv_line = (row["opeid"], row["student_id_number"],
                         row["social_security_number"], str(row["student_first_name"]),
                         row["student_last_name"], row["student_address_line_1"],
                         row["student_address_line_2"], row["student_address_line_3"],
                         row["student_city"], row["student_state_code"],
                         row["student_postal_code"], row["student_country_code"],
                         row["student_email"], row["c_tufe"], row["c_rmbd"],
                         row["c_book"], row["c_tran"], row["c_misc"],
                         row["c_loan"], row["acadyear"])
            print ('Current ID: {0}'.format(currentID))
        csv_line += (row["aid_code"], row["loan_name"], (row["aid_amount"]),
                      (row["c_instgrants"]), row["c_instscholar"],
                      row["c_fedgrants"], row["c_stegrants"], row["c_outsideaid"],
                      row["beginning_date"])
    print (str(csv_line))
        #writer.writerow((row["aid_code"], row["loan_name"], row["aid_amount"], row["c_instgrants"], row["c_instscholar"], row["c_fedgrants"], row["c_stegrants"], row["c_outsideaid"], row["beginning_date"]))

    #phile.close()
    #print open(filename, "r").read()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())