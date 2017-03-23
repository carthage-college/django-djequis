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

from djequis.sql.terradotta import SQL_DATA
from django.template import loader, Context
from django.utils.encoding import smart_bytes

from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL

"""
Terradotta Synchronization
"""
def main():
    # Run SQL statement
    sqlresult = do_sql(SQL_DATA, earl=EARL)

    datetimestr = time.strftime("%Y%m%d-%H%M%S")
    # set directory and filename
    filename=('{}terradotta_{}.csv'.format(
        settings.TERRADOTTA_CSV_OUTPUT,datetimestr
    ))
    new_filename=('{}sis_hr_user_info.txt'.format(
        settings.TERRADOTTA_CSV_OUTPUT
    ))

    phile=open(filename,"w");
    output=csv.writer(phile, dialect='excel-tab')

    output.writerow([
        "UUUID", "LAST_NAME", "FIRST_NAME", "MIDDLE_NAME", "EMAIL",
        "DOB", "GENDER", "CONFIDENTIALITY_INDICATOR", "MAJOR_1",
        "MAJOR_2", "MINOR_1", "MINOR_2", "GPA", "HOME_ADDRESS_LINE1",
        "HOME_ADDRESS_LINE2", "HOME_ADDRESS_LINE3", "HOME_ADDRESS_CITY",
        "HOME_ADDRESS_STATE", "HOME_ADDRESS_ZIP",
        "HOME_ADDRESS_COUNTRY", "PHONE_NUMBER", "CLASS_STANDING",
        "EMERGENCY_CONTACT_NAME", "EMERGENCY_CONTACT_PHONE",
        "EMERGENCY_CONTACT_RELATIONSHIP", "COUNTRY_OF_CITIZENSHIP",
        "ETHNICITY", "PELL_GRANT_STATUS", "HR_TITLE", "HR_CAMPUS_PHONE",
        "HR_FLAG", "PLACE_HOLDER_1", "PLACE_HOLDER_2",
        "PLACE_HOLDER_3", "PLACE_HOLDER_4", "PLACE_HOLDER_5",
        "PLACE_HOLDER_6", "PLACE_HOLDER_7", "PLACE_HOLDER_8",
        "PLACE_HOLDER_9", "PLACE_HOLDER_10", "PLACE_HOLDER_11",
        "PLACE_HOLDER_12", "PLACE_HOLDER_13", "PLACE_HOLDER_14",
        "PLACE_HOLDER_15"
    ])
    # create file
    for row in sqlresult:
        output.writerow(row)
    phile.close()

    # go to our storage directory on this server
    os.chdir(settings.TERRADOTTA_CSV_OUTPUT)
    shutil.copy(filename, new_filename)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
        'host':settings.TERRADOTTA_HOST,
        'username':settings.TERRADOTTA_USER,
        'private_key':settings.TERRADOTTA_PKEY,
        'private_key_pass':settings.TERRADOTTA_PASS,
        'cnopts':cnopts
    }
    # transfer the CSV to scripsafe
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        sftp.put("sis_hr_user_info.txt", preserve_mtime=True)
        sftp.close()

    print "Done"

if __name__ == "__main__":

    sys.exit(main())
