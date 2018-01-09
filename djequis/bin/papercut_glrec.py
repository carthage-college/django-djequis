import os
import sys
import csv
import argparse
from datetime import datetime
import time
from time import gmtime, strftime
import shutil

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
from django.db import connections

# informix environment
os.environ['INFORMIXSERVER'] = settings.INFORMIXSERVER
os.environ['DBSERVERNAME'] = settings.DBSERVERNAME
os.environ['INFORMIXDIR'] = settings.INFORMIXDIR
os.environ['ODBCINI'] = settings.ODBCINI
os.environ['ONCONFIG'] = settings.ONCONFIG
os.environ['INFORMIXSQLHOSTS'] = settings.INFORMIXSQLHOSTS
os.environ['LD_LIBRARY_PATH'] = settings.LD_LIBRARY_PATH
os.environ['LD_RUN_PATH'] = settings.LD_RUN_PATH

from djequis.core.utils import sendmail
from djequis.sql.papercut_glrec import GET_GL_ACCTS
from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY
from djtools.utils.mail import send_mail

DEBUG = settings.INFORMIX_DEBUG
EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Papercut GL
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
def main():
    # Run SQL statement
    sqlresult = do_sql(GET_GL_ACCTS, earl=EARL)
    # for row in sqlresult:
    #     print(row)
        #accountName = row['acct_descr'].split('/',1)[1]
        #print(accountName)
        # acct_name = ("{0}/{1}-{2}-{3}".format(row['acct_descr'].split('/',1)[1],
        #                                      row['fund'],row['func'],row['obj'])
        #             )
        # print(acct_name)
    # set directory and filename

    filename = ('{0}GL_RED_DATA.csv'.format(settings.PAPERCUT_CSV_OUTPUT))
    # create txt file using pipe delimiter
    phile = open(filename,"w");
    output=csv.writer(phile, delimiter="\t")
    # No Header required but used for testing
    output.writerow(["Account Name"])

    # create file
    for row in sqlresult:
        print(row)
        #accountName = row['acct_descr'].split('/',1)[1]
        #print(accountName)
        acct_name = ("{0}/{1}-{2}-{3}".format(row['acct_descr'].split('/',1)[1],
                                             row['fund'],row['func'],row['obj'])
                    )
        output.writerow(acct_name)

    phile.close()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())