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

def file_download():
    # set date and time to be added to the filename
    #datetimestr = time.strftime("%Y%m%d%H%M%S")
    # initializing fileCount
    #fileCount = 1 

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
        # Loop through remote path directory list
        for filename in remotepath:
            remotefile = filename
            print "File Name ==> " + remotefile
            # set source directory for which the common app file will be downloaded to
            source_dir = ('{0}'.format(
                settings.COMMONAPP_CSV_OUTPUT
            ))
            print "Source Directory ==> {0}".format(source_dir)
            localpath = source_dir + remotefile
            print "Local Path ==> {0}".format(localpath)
            # GET file from sFTP server and download it to localpath
            sftp.get(remotefile, localpath)
            print "Downloading files ==> " + remotefile
            #######################################################
            # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
            # from sFTP server
            #######################################################
            sftp.remove(filename)
            #fileCount = fileCount +1
    sftp.close()

def main():
    if not test:
        file_download()
    # set date and time to be added to the filename
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    # initializing fileCount
    fileCount = 1
    source_dir = ('{0}'.format(
        settings.COMMONAPP_CSV_OUTPUT
    ))
    print ('Directory ==> {0}'.format(source_dir))
    localpath = os.listdir(source_dir)
    print "Files found on Carthage server {0}.".format(localpath)
    if localpath != []:
        print ("There was a file(s) found.")
        for localfile in localpath:
            # Local Path == /data2/www/data/commonapp/{filename.txt}
            localpath = source_dir + localfile
            file_size = os.stat(localpath).st_size
            print ('File size ==> {0}'.format(file_size))
            print ('Directory and File(s) ==> {0}'.format(localfile))
            print "Local Path ==> {0}".format(localpath)
            if localfile.endswith(".txt"):
                if file_size > 0:
                    print ('File Name {0} File size ==> {1}'.format(
                        localfile, os.stat(localpath).st_size
                    ))
                    time.sleep(5)
                    destination = ('{0}commonapp-{1}_{2}.txt'.format(
                        settings.COMMONAPP_CSV_ARCHIVED, datetimestr, str(fileCount)
                    ))
                    
                    renamedfile = ('{0}carthage_applications.txt'.format(source_dir))
                    print ('Renamed File: {0}'.format(renamedfile))
                    #######################################################
                    # renaming file fetched from Common App server
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
                    fileCount = fileCount +1
                else:
                    print "The filesize ==> {0} so we need to send an email".format(file_size)
                    #######################################################
                    # Email the filesize is 0 there is no data in the file
                    #######################################################
                    SUBJECT = '[Common Application] failed'
                    BODY = 'File {0} was found but filesize is {1}'.format(localfile, file_size)
                    sendmail(
                        settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
                        BODY, SUBJECT
                    )
            else:
                print "File {0} was found but extension does not end in .txt".format(localfile)
                ############################################################################
                # Found file but the extension does not end in .txt
                ###########################################################################
                SUBJECT = '[Common Application] failed'
                BODY = 'File {0} was found but extension does not end in .txt'.format(localfile)
                sendmail(
                    settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
                    BODY, SUBJECT
                )
    else:
        print ("The directory is empty no file was found.")
        ############################################################################
        # Email there was no file found on the Common App server
        ###########################################################################
        SUBJECT = '[Common Application] failed'
        BODY = "The directory is empty no source file was found."
        sendmail(
            settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
            BODY, SUBJECT
        )
    # set destination directory for which the sql file
    # will be archived to
    archived_destination = ('{0}commonapp_output-{1}.sql'.format(
        settings.COMMONAPP_CSV_ARCHIVED, datetimestr
    ))
    # set name for the sqloutput file
    sqloutput = ('{0}/commonapp_output.sql'.format(os.getcwd()))
    print "Archived Destination ==> {0}".format(archived_destination)
    print "SQL Output file ==> {0}".format(sqloutput)
    #######################################################################
    # Check to see if sql file exists, if not send Email
    #######################################################################
    if os.path.isfile("commonapp_output.sql") != True:
        ###################################################################
        # Email there was no file found on the Common App server
        ###################################################################
        SUBJECT = '[Common Application] failed'
        BODY = "There was no .sql output file to move."
        sendmail(
            settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
            BODY, SUBJECT
        )
    else:
        # rename and move the file to the archive directory
        shutil.move(sqloutput, archived_destination)


if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())