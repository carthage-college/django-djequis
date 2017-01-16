import os
import sys
import pysftp
import csv
import time
import shutil

# python path
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
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

from django.template import loader, Context
from django.utils.encoding import smart_bytes
from djequis.sql.everbridge import STUDENT_UPLOAD
from djequis.sql.everbridge import ADULT_UPLOAD
from djequis.sql.everbridge import FACSTAFF_UPLOAD
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Everbridge Upload
"""
# We currently send all records but future development may require for script to just update records
def main():
    # set dictionary
    dict = {
        'Student': STUDENT_UPLOAD,
        'Adult': ADULT_UPLOAD,
        'FacStaff': FACSTAFF_UPLOAD
        }

    # go to our storage directory on the server
    os.chdir(settings.EVERBRIDGE_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
       'host':settings.EVERBRIDGE_HOST,
       'username':settings.EVERBRIDGE_USER,
       'private_key':settings.EVERBRIDGE_PKEY,
       'cnopts':cnopts
    }

    for key, value in dict.items():
        print key
        sqlresult = do_sql(value, earl=EARL)

        datetimestr = time.strftime("%Y%m%d%H%M%S")
        filename=('{}{}Upload-{}.csv'.format(
            settings.EVERBRIDGE_CSV_OUTPUT,key,datetimestr
        ))

        phile=open(filename,"w");
        output=csv.writer(phile, dialect='excel')

        if key == 'FacStaff': # write header row for FacStaff 
            output.writerow([
                "First Name", "Middle Initial", "Last Name", "Suffix",
                "External ID", "Country", "Business Name", "Record Type",
                "Phone1", "Phone Country1", "Phone2", "Phonecountry2",
                "Email Address1", "Emailaddress2", "SMS1", "SMS1 Country",
                "Custom Field1", "Custom Value1", "Custom Field2",
                "Custom Value2", "Custom Field3", "Custom Value3", "End"
            ])
        else: # write header row for Student and Adult
            output.writerow([
                "First Name", "Middle Initial", "Last Name", "Suffix",
                "External ID", "Country", "Business Name", "Record Type",
                "Phone1", "Phone Country1", "Email Address1", "Emailaddress2",
                "SMS1", "SMS1 Country", "Custom Field1", "Custom Value1",
                "Custom Field2", "Custom Value2", "Custom Field3",
                "Custom Value3", "End"
            ])

        for row in sqlresult:
            output.writerow(row)
            # checking for Bad match in either Student or FacStaff query
            if row.customvalue1 and "Bad match:" in row.customvalue1:
                print (row)
                SUBJECT = '[Everbridge] Bad match: {}, {}'.format(
                    row.lastname, row.firstname
                )
                BODY = '''
                    A bad match exists in the file we are sending to Everbridge.
                    \n\r\n\r{}
                '''.format(str(row))
                sendmail(
                    settings.EVERBRIDGE_TO_EMAIL,
                    settings.EVERBRIDGE_FROM_EMAIL, BODY, SUBJECT
                )

        # SFTP the CSV
        try:
            with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
                sftp.chdir("replace/")

                sftp.put(filename, preserve_mtime=True)
                sftp.close()
        except Exception, e:
            SUBJECT = '[Everbridge SFTP] {} failed'.format(key)
            BODY = 'Unable to PUT upload to Everbridge server.\n\n{}'.format(str(e))
            sendmail(
                settings.EVERBRIDGE_TO_EMAIL,settings.EVERBRIDGE_FROM_EMAIL,
                SUBJECT, BODY
            )

        phile.close()
        print "success: {}".format(key)

    print "Done"

if __name__ == "__main__":

    sys.exit(main())
