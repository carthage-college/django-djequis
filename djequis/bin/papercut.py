import os
import sys
import csv
import argparse
from datetime import datetime
import time
#from time import gmtime, strftime
import shutil
import re

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

from djzbar.utils.informix import do_sql
from djzbar.utils.informix import get_engine
from djzbar.settings import INFORMIX_EARL_TEST
from djzbar.settings import INFORMIX_EARL_PROD

from djtools.fields import TODAY
from djtools.utils.mail import send_mail

DEBUG = settings.INFORMIX_DEBUG

# set up command-line options
desc = """
    Papercut Chargeback
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
def main():
    # set date and time
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # path (/data2/www/data/papercut/) to find the .csv file
    source_dir = ('{0}'.format(settings.PAPERCUT_CSV_OUTPUT))
    # current working directory where the papercut.py resides
    current_dir = os.getcwd()
    # list files within the source_dir
    listfiles = os.listdir(source_dir)
    if listfiles != []:
        for localfile in listfiles:
            # Local Path == /data2/www/data/papercut/{filename.csv}
            localpath = source_dir + localfile
            if localfile.endswith(".csv"):
                # set archive path and new filename that it will be renamed to when archived
                # /data2/www/data/papercut_archives/
                archive_destination = ('{0}modified_papercut_bak_{1}.csv'.format(
                    settings.PAPERCUT_CSV_ARCHIVED, datetimestr
                ))
                # rename file to be processed
                # /data2/www/data/papercut/papercut.csv
                orig_papercut_file = ('{0}papercut.csv'.format(source_dir))
                # file name for new file being created
                # /data2/www/data/papercut/monthly-papercut.csv
                modified_papercut_file = ('{0}monthly-papercut.csv'.format(source_dir))
                # the filename renamed to papercut.csv
                shutil.move(localpath, orig_papercut_file)
                # get current year
                currentYear = datetime.now().year
                # get current date and time
                mydate = datetime.now()
                # returns the short notation for month name + currentYear
                currentMonthYear = mydate.strftime("%b") + str(currentYear)
                # modified papercut output csv file
                with open(modified_papercut_file, 'wb') as modified_papercut_csv:
                    writer = csv.writer(modified_papercut_csv)
                    # open original papercut input csv file for reading 
                    with open(orig_papercut_file,'r') as orig_papercut_csv:
                        for i in range(2):
                            orig_papercut_csv.next()
                        #print(i)
                        reader = csv.DictReader(orig_papercut_csv, delimiter=',')
                        # creates header row in csv file
                        headrow = ("Description", "PostngAccnt", "Amount")
                        # writes file header elements
                        writer.writerow(headrow)
                        for row in reader:
                            try:
                                # split account name to remove shared account parent name
                                #accountName = row['Shared Account Parent Name'].split('/',1)[1]
                                #accountName2 = 'r(?:\/)(.\S+)'.format(row['Shared Account Parent Name'])
                                #accountName2 = accountName.split('\S+', 1)[0]
                                accountName2 = re.split(r'\/\S+', row['Shared Account Parent Name'],2)[1]
                                #accountName2 = re.split(r'\#', accountName,1)[1]
                                #accountName = re.split(r'\/\s+ ', row['Shared Account Parent Name'])
                                print(accountName2)
                                print row['Cost']
                                csv_line = ("{0} print-copy".format(currentMonthYear),
                                    row['Shared Account Parent Name'].split('/',1)[1],
                                    row['Cost'])
                                writer.writerow(csv_line)
                            #except IndexError:
                            except Exception as e:
                                print "Exception: {0}".format(str(e))
                                # Email there was an exception error while processing .csv
                                # SUBJECT = '[Papercut] modified file'
                                # BODY = "There was an exception error: {0}".format(str(e))
                                # sendmail(
                                #     settings.PAPERCUT_TO_EMAIL,settings.PAPERCUT_FROM_EMAIL,
                                #     BODY, SUBJECT
                                # )
                    # close orig_papercut_csv
                    orig_papercut_csv.close()
                    # close modified_papercut_csv
                modified_papercut_csv.close()
                
                os.remove(orig_papercut_file)
                os.remove(modified_papercut_file)
                '''
                # remove original papercut.csv file
                os.remove(orig_papercut_file)
                # archive monthly-papercut.csv file
                shutil.copy(modified_papercut_file, archive_destination)

                #modifiedfile = ('{0}/monthly-papercut.csv'.format(current_dir))
                #print ('Modified File Name: {0}'.format(modifiedfile))
                #shutil.move(modified_papercut_file, orig_papercut_file)

    # email with file attachment
    #file_attach = '{0}papercut.csv'.format(source_dir)
    file_attach = modified_papercut_file
    request = None
    recipients = settings.PAPERCUT_TO_EMAIL
    subject = "[Papercut] with attachment"
    femail = settings.PAPERCUT_FROM_EMAIL
    template = 'papercut/email.html'
    bcc = 'ssmolik@carthage.edu'
    send_mail(
        request, recipients, subject, femail, template, bcc, attach=file_attach
    )
    # delete monthly-papercut.csv file
    os.remove(modified_papercut_file)
    '''
if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
