import os
import sys
import pysftp
import csv
import time
import argparse
import shutil

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
    # set date and time to be added to the filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # initializing fileCount
    fileCount = 1 

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    ###########################################################################
    # External connection information for Common Application server
    ###########################################################################
    XTRNL_CONNECTION = {
       'host':settings.COMMONAPP_HOST,
       'username':settings.COMMONAPP_USER,
       'password':settings.COMMONAPP_PASS,
       'cnopts':cnopts
    }
    ###########################################################################
    # sFTP GET downloads the file from Common App file from server 
    # and saves in source directory. When applications have been processed
    # the source file will be archived.
    ###########################################################################
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        # Remote Path is the Common App server and once logged in we fetch directory listing
        remotepath = sftp.listdir()
        print "sFTP files found on Common App server {0}.".format(remotepath)
        #######################################################################
        # Check if file list found in remote path is NOT empty
        # If no file is found then send an email
        #######################################################################
        if remotepath != []:
            print ("There was a file(s) found.")
            # Loop through remote path directory list
            for filename in remotepath:
                print "File Name ==> " + filename
                # Check to see that the file ends with .txt
                if filename.endswith(".txt"):
                    # set variable to get the file attributes (size)
                    sftpstat = sftp.stat(filename)
                    # check to make sure the file has data by checking the size
                    if sftpstat.st_size > 0:
                        # set destination directory for which the common app file will be archived to
                        destination = ('{0}commonapp-{1}_{2}.txt'.format(settings.COMMONAPP_CSV_ARCHIVED, datetimestr, str(fileCount)))
                        # set source directory for which the common app file will be downloaded to
                        source_dir = ('{0}'.format(settings.COMMONAPP_CSV_OUTPUT))
                        # Print filesize
                        print "Filesize ==> {0}".format(sftpstat.st_size)
                        # Local Path == /data2/www/data/commonapp/{filename.txt}
                        localpath = source_dir + filename
                        print "Local Path ==> {0}".format(localpath)
                        # GET file from sFTP server and download it to localpath
                        sftp.get(filename, localpath)
                        print "Downloading files ==> " + filename
                        # Renamed File == /data2/www/data/commonapp/carthage_applications.txt
                        renamedfile = ('{0}carthage_applications.txt'.format(source_dir))
                        print ('Renamed File: {0}'.format(renamedfile))

                        #######################################################
                        # renaming file coming in from Common App
                        # The filename comming in %m_%d_%y_%h_%i_%s_Applications(%c).txt
                        # The filename renamed to carthage_applications.txt
                        #######################################################
                        shutil.move(localpath, renamedfile)
                        print "The path and renamed file ==> " + renamedfile
                        time.sleep(10)
                        print "The path and archived filename ==> " + destination

                        #######################################################
                        # Rename the Archive file
                        # renames carthage_applications.txt to commonapp-%Y%m%d%H%M%S.txt
                        #######################################################
                        shutil.move(renamedfile, destination)
                        #fileCount = fileCount +1
                        time.sleep(10)
                        print "Deleting file from sFTP ==> " + filename

                        #######################################################
                        # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
                        # from sFTP server
                        #######################################################
                        sftp.remove(filename)
                        fileCount = fileCount +1
                    else:
                        print "The filesize ==> {0} so we need to send an email".format(sftpstat.st_size)
                        #######################################################
                        # Email the filesize is 0 there is no data in the file
                        #######################################################
                        SUBJECT = '[Common Application sFTP] failed'
                        BODY = 'File {0} was found but filesize is {1}'.format(filename, sftpstat.st_size)
                        sendmail(
                            settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
                            BODY, SUBJECT
                        )
                else:
                    ############################################################################
                    # Found file but the extension does not end in .txt
                    ###########################################################################
                    SUBJECT = '[Common Application sFTP] failed'
                    BODY = 'File {0} was found but extension does not end in .txt'.format(filename)
                    sendmail(
                        settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
                        BODY, SUBJECT
                    )
        else:
            print ("The directory is empty no file was found.")
            ############################################################################
            # Email there was no file found on the Common App server
            ###########################################################################
            SUBJECT = '[Common Application sFTP] failed'
            BODY = "The source file was not found on the Common App server."
            sendmail(
                settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
                BODY, SUBJECT
            )
    sftp.close()

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
