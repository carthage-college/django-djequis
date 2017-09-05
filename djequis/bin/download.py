import os
import sys
import pysftp
import csv
import time
import argparse
import shutil
import glob

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

# set up command-line options
desc = """
    Download Common Application Download via sftp
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def main():
    ##################################################################################
    # Creating variables for Source, destination directories and date & time stamp
    ##################################################################################
    datetimestr = time.strftime("%Y%m%d%H%M%S") # set date and time to be added to the filename
    source_dir = ('{0}'.format(settings.COMMONAPP_CSV_OUTPUT))
    destination = ('{0}commonapp-{1}.txt'.format(settings.COMMONAPP_CSV_ARCHIVED, datetimestr))

    # go to our storage directory on the server
    filename = ('08_03_2017_16_05_11_Applications(3).txt')
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    ##################################################################################
    # External connection information for Common Application server
    ##################################################################################
    XTRNL_CONNECTION = {
       'host':settings.COMMONAPP_HOST,
       'username':settings.COMMONAPP_USER,
       'password':settings.COMMONAPP_PASS,
       'cnopts':cnopts
    }
    ##################################################################################
    # sFTP GET downloads the file from Common App file from server 
    # and saves in specfied directory
    ##################################################################################
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        for filename in sftp.listdir():
          try:
              if filename.endswith(".txt"):
                localpath = source_dir + '/' + filename
                print "Downloading files ==> " + filename
                sftp.get(filename, localpath)
                renamedFile = ('{0}carthage_applications.txt'.format(source_dir))
                print ('Renamed File: {0}'.format(renamedFile))
                shutil.move(localpath, renamedFile)
          except IOError as e:
              print e
        sftp.close()
    ##################################################################################
    # This will rename and move the file to archives directory
    ##################################################################################
    for file in os.listdir(source_dir):
        if file.endswith(".txt"):
            currentfilename=('{0}{1}'.format(source_dir,file))
            print ('File: {0}'.format(currentfilename))
            #changedfilename=('{0}{1}'.format(destination))
            print ('New File: {0}'.format(destination))
            #os.rename(file, philename)
            shutil.move(currentfilename, destination)
    ##################################################################################
    # Email
    ##################################################################################
        # SUBJECT = '[Common Application SFTP] {} failed'.format(key)
        # BODY = 'Unable to GET upload to Common Application server.\n\n{}'.format(str(e))
        # sendmail(
        #     settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
        #     SUBJECT, BODY
        # )

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
