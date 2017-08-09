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
    sqlresult = do_sql(WIS_ACT_284_SQL, earl=EARL)

    control = None
    line = None

    for x in sqlresult:
        #print(x)
        if x[1] == control:
            line =+ x[1]
            print(control)
        else:
            line = x[1]
            control = x[1]
            #print(line)
        #print(control)

    #where control is the value in your row that you will use to determine if you have the same student and thus you put the data on the same line or it is a different student and you create a new line

    # for row in sqlresult:
    #     #print (row)
    #     if row[1] == row[1]:
    #         print(row[1])

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())