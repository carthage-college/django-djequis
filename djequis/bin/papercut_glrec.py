import os
import sys
import csv
import argparse
#from datetime import datetime
import time
#from time import gmtime, strftime
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
    GL Account Names for Papercut
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
def main():
    # execute SQL statement
    sqlresult = do_sql(GET_GL_ACCTS, earl=EARL)
    # formatting date and time string 
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # set directory and filename
    filename = ('{0}glrec_data.csv'.format(settings.PAPERCUT_CSV_OUTPUT))
    # set destination path and new filename that it will be renamed to when archived
    archive_destination = ('{0}{1}_{2}.csv'.format(
        settings.PAPERCUT_CSV_ARCHIVED,'glrec_data_bak',datetimestr
    ))
    # opens a file for writing
    with open(filename,'w') as glrecfile:
        for row in sqlresult:
            #print(row)
            #acct_desc = row['acct_descr'].split('/',1)[1]
            # creates a formatted string
            accountName = ("{0}/{1}-{2}-{3}".format(row['acct_descr'].split('/',1)[1],
                                                 row['fund'],row['func'],row['obj'])
                        )
            print(accountName)
            # writes a formatted string to the file
            glrecfile.write('{0}\n'.format(accountName))
    # close file
    glrecfile.close()

    # sends email attachment
    file_attach = '{0}glrec_data.csv'.format(settings.PAPERCUT_CSV_OUTPUT)
    request = None
    recipients = settings.PAPERCUT_TO_EMAIL
    subject = "[GL Account Names] attachment"
    femail = settings.PAPERCUT_FROM_EMAIL
    template = 'papercut/glrec_email.html'
    bcc = 'ssmolik@carthage.edu'
    send_mail(
        request, recipients, subject, femail, template, bcc, attach=file_attach
    )
    # renaming old filename to newfilename and move to archive location
    shutil.copy(filename, archive_destination)
    # sleep for 3 seconds
    #time.sleep(3)
    # delete file
    #os.remove(filename)

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())