import os
import sys
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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djequis.settings')

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

from djequis.sql.wisact284 import WIS_ACT_284_SQL, WIS_ACT_284_RC_SQL
from djequis.core.utils import sendmail
from djequis.core.financialaid.utils import csv_gen
from djzbar.utils.informix import do_sql

EARL = settings.INFORMIX_EARL
DEBUG = settings.INFORMIX_DEBUG

###############################################################################
# The objective of the School College Cost Meter (CCM) File is to help schools
# provide detailed student information to Great Lakes in a standard format that
# correctly populates the College Cost Meter.
#
# The School College Cost Meter File will list all students to which
# Great Lakes will send an email or letter detailing required
# state law information.
###############################################################################
desc = """
    Wisconsin ACT 284
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--spring",
    action='store_true',
    help="spring term only",
    dest='spring'
)
parser.add_argument(
    "--dispersed",
    action='store_true',
    help="amount status = AD",
    dest='dispersed'
)
parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest='test'
)


def main():

    # spring term only
    if spring:
        sql = WIS_ACT_284_RC_SQL
    else:
        sql = WIS_ACT_284_SQL
    # determines if aid has been despersed
    if dispersed:
        sql = sql(amt_stat = '"AD"')
    else:
        sql = sql(amt_stat = '"AA","AD","AP","EA"')

    # run getaid_sql SQL statement
    sqlresults = do_sql(sql, earl=EARL)
    # if there are no results send email
    if sqlresults is None:
        # send email
        SUBJECT = "[Wisconsin Act 284] College Cost Meter file"
        BODY = "Funds have not been dispersed.\n\n"
        sendmail(
            settings.WISACT_TO_EMAIL, settings.WISACT_FROM_EMAIL,
            BODY, SUBJECT
        )
    else:
        # set date and time to be added to the filename string
        datetimestr = time.strftime('%Y%m%d%H%M%S')
        # set directory and College Cost Meter file where to be stored
        ccmfile = (
            '{0}CCM-{1}.csv'.format(
                settings.WISACT_CSV_OUTPUT, datetimestr
            )
        )
        # opens ccmfile in write mode to add the comment
        wisactfile = open(ccmfile,'w');
        # creating a csv writer object
        writer = csv.writer(wisactfile)

        # generate the CSV file
        csv_gen(sqlresults, writer, test)

        # close the file
        wisactfile.close()

if __name__ == '__main__':
    args = parser.parse_args()
    dispersed = args.dispersed
    spring = args.spring
    test = args.test

    sys.exit(main())
