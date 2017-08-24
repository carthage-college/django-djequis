import os
import sys
import pysftp
import csv
import time
import argparse

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

    filename=('08_03_2017_16_05_11_Applications(3).txt')
    # destination = ('{0}'.format(
    #         settings.COMMONAPP_CSV_OUTPUT
    #     ))
    # go to our storage directory on the server
    #os.chdir(settings.COMMONAPP_CSV_OUTPUT)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
       'host':settings.COMMONAPP_HOST,
       'username':settings.COMMONAPP_USER,
       'password':settings.COMMONAPP_PASS,
       'cnopts':cnopts
    }
    # SFTP GET the Common App file
    #for filename in sftp.listdir():
    # try:
    #     if filename.startswith('08_03_2017_16_05_11_Applications(3).txt'):
    #         localpath = destination + '/' + filename
    #         print "Downloading files ==> " + filename
    #         sftp.get(filename, localpath)
    # except IOError as e:
    #     print e
    # sftp.close()
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            #sftp.chdir("replace/")
            directories_data = sftp.listdir()
            print (directories_data)
            # if filename in directories_data:
            #     sftp.get(filename, preserve_mtime=True) # get a remote file
            #     print "Downloading files ==> " + filename
            # sftp.close()
    except Exception, e:
        print e
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
