import os
import sys
import pysftp
import csv
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
from djequis.sql.maxient import DEMOGRAPHIC_DATA
from djequis.core.utils import sendmail
from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL

# set up command-line options
desc = """
    Maxient Upload
"""
def main():
    # go to our storage directory on the server
    os.chdir(settings.MAXIENT_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # SFTP connection information
    XTRNL_CONNECTION = {
       'host':settings.MAXIENT_HOST,
       'username':settings.MAXIENT_USER,
       'private_key':settings.MAXIENT_PKEY,
       'cnopts':cnopts
    }
    # Run SQL statement
    sqlresult = do_sql(DEMOGRAPHIC_DATA, earl=EARL)
    # set directory and filename
    filename=('{}CARTHAGE_DEMOGRAPHICS_DATA.txt'.format(
        settings.MAXIENT_CSV_OUTPUT
    ))
    # create txt file using pipe delimiter
    phile=open(filename,"w");
    output=csv.writer(phile, delimiter="|")
    # No Header required but used for testing
    #output.writerow([
    #    "Carthage ID", "Username", "Last Name", "First Name",
    #    "Middle Name", "Date of Birth", "Gender", "Ethnicity",
    #    "Building", "Room Number", "Local Mailing Address",
    #    "Local City", "Local State", "Local Zip", "Local Phone",
    #    "Cell Phone", "Permanent Address", "Permanent City",
    #    "Permanent State", "Permanent Zip", "Permanent Country",
    #    "Permanent Phone", "Emergency Contact", "Email Address",
    #    "Classification", "Academic Major", "Academic Advisor",
    #    "GPA Recent", "GPA Cumulative", "Athlete", "Greek", "Honors",
    #    "ROTC Vet", "Last Update"
    #])
    #print (sqlresult)
    # create file
    if sqlresult is not None:
        for row in sqlresult:
            output.writerow(row)
    else:
        print ("No values in list")
    phile.close()
    # SFTP the .txt file
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            sftp.chdir("incoming/")
            sftp.put(filename, preserve_mtime=True)
            sftp.close()
    except Exception, e:
        SUBJECT = '[Maxient SFTP] MAXIENT UPLOAD failed'
        BODY = 'Unable to PUT upload to Maxient server.\n\n{}'.format(str(e))
        sendmail(
            settings.MAXIENT_TO_EMAIL,settings.MAXIENT_FROM_EMAIL,
            SUBJECT, BODY
        )
    print "success: MAXIENT UPLOAD"

if __name__ == "__main__":

    sys.exit(main())