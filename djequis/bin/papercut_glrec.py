import os
import sys
import argparse
import time
import shutil

# django settings for shell environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

# prime django
import django
django.setup()

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

from djequis.sql.papercut_glrec import GET_GL_ACCTS
from djzbar.utils.informix import do_sql

from djtools.utils.mail import send_mail

TO = settings.PAPERCUT_TO_EMAIL
BCC = settings.PAPERCUT_BCC_EMAIL
FROM = settings.PAPERCUT_FROM_EMAIL
EARL = settings.INFORMIX_EARL
TEMPLATE = 'papercut/glrec_email.html'

# set up command-line options
desc = """
    Papercut Account Names from GL
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
    datetimestr = time.strftime("%Y-%m-%d")
    # set directory and filename
    filename = ('{0}gl_data/glrec_data.csv'.format(
        settings.PAPERCUT_CSV_OUTPUT)
    )
    # set destination path and new filename that it will be renamed
    # to when archived
    archive_destination = ('{0}/gl_data/{1}_{2}.csv'.format(
        settings.PAPERCUT_CSV_ARCHIVED,'glrec_data_bak',datetimestr)
    )
    # opens a file for writing
    with open(filename,'w') as glrecfile:
        for row in sqlresult:
            try:
                # creates a formatted string
                accountName = (
                    "{0}/{1}-{2}-{3}".format(row['acct_descr'].split('/',1)[1],
                    row['fund'],row['func'],row['obj'])
                )
                # writes a formatted string to the file
                glrecfile.write('{0}\n'.format(accountName))
            except Exception as e:
                #print "Exception: {0}".format(str(e))
                # Email that there was an exception error while processing .csv
                SUBJECT = "[Papercut] GL Exception Error"
                BODY = "There was an exception error: {0}".format(str(e))
                send_mail(None, TO, SUBJECT, FROM, TEMPLATE, BODY, bcc=BCC)

    # close file
    glrecfile.close()
    # removed for now S. Smolik 1/19/2018
    # sends email attachment
    # file_attach = '{0}glrec_data.csv'.format(settings.PAPERCUT_CSV_OUTPUT)
    # subject = "[GL Account Names] attachment"
    # send_mail(
    #   None, TO, SUBJECT, FROM, TEMPLATE, BODY, bcc=BCC, attach=file_attach
    #)
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
