import os
import sys
import csv
import argparse
from datetime import datetime
import time
from time import gmtime, strftime
import shutil
from itertools import islice

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

#from djequis.core.utils import sendmail

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
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    print ('Date and Time ==> {0}'.format(time.strftime("%A, %B %d %Y")))
    # path for which to find the .csv file
    # /data2/www/data/papercut/
    source_dir = ('{0}'.format(
        settings.PAPERCUT_CSV_OUTPUT
    ))
    print ('Source Directory ==> {0}'.format(source_dir))
    # template_dir = ('{0}'.format(
    #     settings.PAPERCUT_CSV_TEMPLATE
    # ))
    # current directory where the papercut.py resides
    # /home/ssmolik/django_dev/django-djequis/djequis/bin
    current_dir = os.getcwd()
    print ('Current Working Directory ==> {0}'.format(current_dir))
    # print ('Template Directory ==> {0}'.format(template_dir))
    #print "Files found in Template directory {0}.".format(os.listdir(template_dir))
    # list files within the source_dir
    localpath = os.listdir(source_dir)
    print "Files found in Papercut directory {0}.".format(localpath)
    if localpath != []:
        print ("There was a file(s) found.")
        for localfile in localpath:
            # Local Path == /data2/www/data/papercut/{filename.txt}
            localpath = source_dir + localfile
            print "Local Path ==> {0}".format(localpath)
            # name of the file found in /data2/www/data/papercut/
            print ('Directory and File(s) ==> {0}'.format(localfile))
            if localfile.endswith(".csv"):
                # set destination path and new filename that it will be renamed to when archived
                # /data2/www/data/papercut_archives/
                archived_dir = ('{0}papercut-{1}.csv'.format(
                    settings.PAPERCUT_CSV_ARCHIVED, datetimestr
                ))
                # renamed file name to be processed
                # /data2/www/data/papercut/papercut.csv
                renamedfile = ('{0}papercut.csv'.format(source_dir))
                print ('Renamed File: {0}'.format(renamedfile))
                # renaming file fetched from Common App server
                # The filename comming in %m_%d_%y_%h_%i_%s_Applications(%c).txt
                # The filename renamed to carthage_applications.txt
                shutil.move(localpath, renamedfile)
                # Email there was no file found on the Common App server
                # SUBJECT = '[Papercut] modified file'
                # BODY = "Here is the new modified papercut file."
                # sendmail(
                #     settings.PAPERCUT_TO_EMAIL,settings.PAPERCUT_FROM_EMAIL,
                #     BODY, SUBJECT
                # )
                
                # print "The path and renamed file ==> " + renamedfile
                # print "The path and archived filename ==> " + destination
                # get current year
                currentYear = datetime.now().year
                #print ('Current Year: {0}'.format(currentYear))
                # get current date and time
                mydate = datetime.now()
                #print ('MyDate: {0}'.format(mydate))
                # returns the short notation for month name + currentYear
                currentMonthYear = mydate.strftime("%b") + str(currentYear)
                print ('Current Month/Year: {0}'.format(currentMonthYear))
                # open original papercut input csv file for reading 
                orig_papercut_csv = open (renamedfile,"r")
                # modified papercut output csv file
                with open('Monthly-Modified.csv', 'wb') as modified_papercut_csv:
                    writer = csv.writer(modified_papercut_csv)
                    # open original papercut input csv file for reading 
                    with open(renamedfile,'r') as orig_papercut_csv:
                        for i in range(2):
                            orig_papercut_csv.next()
                        print(i)
                        reader = csv.DictReader(orig_papercut_csv, delimiter=',')
                        
                        # creates header row in csv file
                        headrow = ("Description", "PostngAccnt", "Amount")
                        # writes file header elements
                        writer.writerow(headrow)
                        for row in reader:
                            try:
                                # split account name to remove shared account parent name
                                accountName = row['Shared Account Parent Name'].split('/',1)[1]
                                print(accountName)
                                print row['Cost']
                                csv_line = ("{0} print-copy".format(currentMonthYear),
                                    row["Shared Account Parent Name"].split('/',1)[1],
                                    row["Cost"])
                                writer.writerow(csv_line)
                            except IndexError:
                                #print("Error index")
                                pass # handle error; there's empty element
                            continue
                orig_papercut_csv.close()
                modifiedfile = ('{0}/Monthly-Modified.csv'.format(current_dir))
                shutil.move(modifiedfile, renamedfile)
    #request, recipients, subject, femail, template, data, bcc=None, content='html', attach=False
    phile = '{0}papercut.csv'.format(source_dir)
    request = None
    recipients = settings.PAPERCUT_TO_EMAIL
    #message = "Here is the new modified papercut file."
    subject = "[Papercut] with attachment"
    femail = settings.PAPERCUT_FROM_EMAIL
    template = 'papercut/email.html'
    #to_email = settings.PAPERCUT_TO_EMAIL
    #template = 'papercut/email.html'
    #template = '{0}email.html'.format(template_dir)
    #data = {'student':student_data,}
    #data = {'object': 'steve', 'email': 'emailaddress', 'test': 'test'}
    bcc = 'ssmolik@carthage.edu'
    send_mail(
        request, recipients, subject, femail, template, bcc, attach=phile
    )


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())