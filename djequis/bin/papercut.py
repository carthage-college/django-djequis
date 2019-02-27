import os
import sys
import csv
import argparse
from dateutil.relativedelta import relativedelta
import time
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

from djtools.fields import TODAY
from djtools.utils.mail import send_mail

TO = settings.PAPERCUT_TO_EMAIL
FROM = settings.PAPERCUT_FROM_EMAIL
BCC = settings.PAPERCUT_BCC_EMAIL
TEMPLATE = 'papercut/email.html'

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
    # Returns the same day of last month if possible otherwise end of month
    # (eg: March 31st->29th Feb an July 31st->June 30th)
    last_month = TODAY - relativedelta(months=1)
    # create string of short notation for month name and year
    month_year = format(last_month, '%b%Y')
    # source path (/data2/www/data/papercut/) to find the .csv file
    source_dir = ('{}'.format(settings.PAPERCUT_CSV_OUTPUT))
    # list files within the source_dir
    listfiles = os.listdir(source_dir)
    # file flag to indicate if we found a csv file or not
    phile = False
    for localfile in listfiles:
        # Local Path == /data2/www/data/papercut/{filename.csv}
        localpath = source_dir + localfile
        if localfile.endswith(".csv"):
            print("localpath = {}".format(localpath))
            # set archive path and new filename to which it will be renamed
            # when archived in /data2/www/data/papercut_archives/
            archive_destination = ('{0}modified_papercut_bak_{1}.csv'.format(
                settings.PAPERCUT_CSV_ARCHIVED, datetimestr
            ))
            print("archive_destination = {}".format(archive_destination))
            # rename file to be processed
            # /data2/www/data/papercut/papercut.csv
            orig_papercut_file = ('{}papercut.csv'.format(source_dir))
            print("orig_papercut_file = {}".format(orig_papercut_file))
            # file name for new file being created
            # /data2/www/data/papercut/monthly-papercut.csv
            modified_papercut_file = (
                '{}monthly-papercut.csv'.format(source_dir)
            )
            print("modified_papercut_file = {}".format(modified_papercut_file))
            # the filename renamed to papercut.csv
            shutil.move(localpath, orig_papercut_file)
            # modified papercut output csv file
            total_cost = 0
            with open(modified_papercut_file, 'wb') as modified_papercut_csv:
                writer = csv.writer(modified_papercut_csv)
                # open original papercut input csv file for reading
                with open(orig_papercut_file,'r') as orig_papercut_csv:
                    for i in range(2):
                        orig_papercut_csv.next()
                    reader = csv.DictReader(orig_papercut_csv, delimiter=',')
                    for row in reader:
                        try:
                            # split account name to remove shared account
                            # parent name
                            ###################################################
                            # the objective is to remove everything before the
                            # slash (/) including and after a certain character
                            # in the string \s* will helps to match also the
                            # preceding vertical or horizontal space character
                            ###################################################
                            #accountName2 = re.sub(
                                #r'(.*)/(.*)(.*)#(.*)',
                                #row['Shared Account Parent Name']
                            #)
                            accountName = re.sub(
                              r'\s*#.*', '',
                              row['Shared Account Parent Name'].split('/',1)[1]
                            )
                            #print(accountName)
                            #print row['Cost']
                            # sum of the Cost field
                            total_cost += float(row['Cost'])
                            csv_line = (
                                "{} print-copy".format(month_year), accountName,
                                row['Cost']
                            )
                            writer.writerow(csv_line)
                        except Exception as e:
                            #print "Exception: {}".format(str(e))
                            # Email there was an exception error while
                            # processing .csv
                            SUBJECT = "[Papercut] modified file"
                            BODY = "There was an exception error: {}".format(
                                str(e)
                            )
                            send_mail(
                                None,TO,SUBJECT,FROM,TEMPLATE,BODY,bcc=BCC
                            )
                    # convert positve interger to negative interger
                    total_cost = (total_cost * -1)
                    # writes the last line for the total cost
                    csv_line = (
                        "{} print-copy".format(month_year), "1-509-73140",
                        (total_cost)
                    )
                    writer.writerow(csv_line)
                # close orig_papercut_csv
                orig_papercut_csv.close()
            # close modified_papercut_csv
            modified_papercut_csv.close()
            # remove original papercut.csv file
            os.remove(orig_papercut_file)
            # archive monthly-papercut.csv file
            shutil.copy(modified_papercut_file, archive_destination)
            # send email with file attachment
            file_attach = modified_papercut_file
            subject = "[Papercut] with attachment"
            send_mail(
                None, TO, subject, FROM, TEMPLATE, bcc=BCC,
                attach=file_attach
            )
            # delete monthly-papercut.csv file
            os.remove(modified_papercut_file)
            phile = False
            # break tells whether we have found the .csv file
            break
    if not phile:
        # no file was found send email
        SUBJECT = '[Papercut] failed: no file found'
        BODY = 'No .csv file was found'
        send_mail(None, TO, SUBJECT, FROM, TEMPLATE, BODY, bcc=BCC)

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
