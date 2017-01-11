import os
import sys
import pysftp
import csv
import time
import shutil

# python paths
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
# django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")
# informix
os.environ['INFORMIXSERVER'] = 'wilson'
os.environ['DBSERVERNAME'] = 'wilson'
os.environ['INFORMIXDIR'] = '/opt/ibm/informix'
os.environ['ODBCINI'] = '/etc/odbc.ini'
os.environ['ONCONFIG'] = 'onconf.cars'
#os.environ['ONCONFIG'] = 'onconf.carstrain'
os.environ['INFORMIXSQLHOSTS'] = '/opt/ibm/informix/etc/sqlhosts'
os.environ['LD_LIBRARY_PATH'] = '$INFORMIXDIR/lib:$INFORMIXDIR/lib/esql:$INFORMIXDIR/lib/tools:/usr/lib/apache2/modules:$INFORMIXDIR/lib/cli'
os.environ['LD_RUN_PATH'] = '/opt/ibm/informix/lib:/opt/ibm/informix/lib/esql:/opt/ibm/informix/lib/tools:/usr/lib/apache2/modules'

import django
django.setup()

from django.conf import settings
from django.template import loader, Context
from django.utils.encoding import smart_bytes
from djequis.sql.everbridge import STUDENT_UPLOAD
from djequis.sql.everbridge import ADULT_UPLOAD
from djequis.sql.everbridge import FACSTAFF_UPLOAD
from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Everbridge Upload
"""

def main():
    dict = {'Student': STUDENT_UPLOAD, 'Adult': ADULT_UPLOAD, 'FacStaff': FACSTAFF_UPLOAD}
    for key, value in dict.items():

        sqlresult = do_sql(value, earl=EARL)

        datetimestr = time.strftime("%Y%m%d%H%M%S")
        filename=('{}{}Upload-{}.csv'.format(
            settings.EVERBRIDGE_CSV_OUTPUT,key,datetimestr
        ))

        phile=open(filename,"w");
        output=csv.writer(phile, dialect='excel')

        if key == 'FacStaff':
            output.writerow([
            "First Name", "Middle Initial", "Last Name", "Suffix",
            "External ID", "Country", "Business Name", "Record Type",
            "Phone1", "Phone Country1", "Phone2", "Phonecountry2",
            "Email Address1", "Emailaddress2", "SMS1", "SMS1 Country",
            "Custom Field1", "Custom Value1", "Custom Field2",
            "Custom Value2", "Custom Field3", "Custom Value3", "End"
            ])
        else:
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

        # go to our storage directory on this server
        os.chdir(settings.EVERBRIDGE_CSV_OUTPUT)
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        XTRNL_CONNECTION = {
           'host':settings.EVERBRIDGE_HOST,
           'username':settings.EVERBRIDGE_USER,
           'private_key':settings.EVERBRIDGE_PKEY,
           'cnopts':cnopts
        }
        # transfer the CSV
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            sftp.chdir("replace/")

        sftp.put(filename, preserve_mtime=True)

    sftp.close()
    phile.close()

if __name__ == "__main__":

    sys.exit(main())
