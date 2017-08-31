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
    datetimestr = time.strftime("%Y%m%d%H%M%S")
    #newfilename = ('08_03_2017_16_05_11_Applications(3).txt')
    new_file_name = ('carthage_applications.txt')
    source_dir = ('{0}'.format(settings.COMMONAPP_CSV_OUTPUT))
    destination = ('{0}commonapp-{1}.txt'.format(settings.COMMONAPP_CSV_ARCHIVED, datetimestr))

    # go to our storage directory on the server
    #os.chdir(settings.COMMONAPP_CSV_OUTPUT)

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    ##################################################################################
    # External connection information
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
    # This function renames and moves the files to archives directory
    ##################################################################################

    for file in os.listdir(source_dir):
        if file.endswith(".txt"):
            currentfilename=('{0}{1}'.format(source_dir,file))
            print ('File: {0}'.format(currentfilename))
            #changedfilename=('{0}{1}'.format(destination))
            print ('New File: {0}'.format(destination))
            #os.rename(file, philename)
            shutil.move(currentfilename, destination)
    
    # try:
    # This function calls the file_download function 
# and moves the files to required directory. If 
# using shutil.move() then it copies permissions 
# also which is not desirable always.

    #     with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
    #         #sftp.chdir("replace/")
    #         directories_data = sftp.listdir()
    #         print (directories_data)
    #         commonappfile = (directories_data)
            # localpath = destination + filename
            # print "Downloading files ==> " + filename
            # sftp.get(remote_file, preserve_mtime=True)
            # if filename.endswith(".txt"):
            #     shutil.move(filename,source_dir)
            #print ('Original File Name: {0}'.format(filename))
           # print ('New File Name: {0}'.format(new_file_name))
            
            #print ('New Directory: {0}'.format(archived_destination))
            #shutil.move(new_file_name,archived_destination)
            #source_dir = '/path/to/dir/with/files' #Path where your files are at the moment
            #dst = '/path/to/dir/for/new/files' #Path you want to move your files to
            #os.rename('path/to/file.txt', 'path/to/new/directory/file.txt')
            #
            #**for file in os.listdir(source_dir):
                #**if file.endswith(".txt"):
                    #**currentfilename=('{0}{1}'.format(source_dir,file))
                    #**print ('File: {0}'.format(currentfilename))
                    #changedfilename=('{0}{1}'.format(destination))
                    #**print ('New File: {0}'.format(destination))
                    #os.rename(file, philename)
                    #**shutil.move(currentfilename, destination)
            
            
            
            
            #     if file.endswith(".txt"):
            #         #print(os.path.join(source_dir, file))
            #         print ('Files: {0}'.format(file))
            #         shutil.copy2(file, destination)
            # files = glob.iglob(os.path.join(source_dir, "*.txt"))
            # for file in files:
            #     if os.path.isfile(file):
            #         # filename_without_ext = os.path.splitext(file)[0]
                    #print ('File Name: {0}'.format(file))
                    #os.rename(file, newfilename)
                    #
                    #print ('Archieved File Name: {0}'.format(os.path.join(destination, file)))
                    #os.rename(os.path.join(destination, file),os.path.join(destination, newfilename))
            #         #shutil.copy(path, file + "_" + str(i) + extension)
            # for filename in os.listdir(destination):
            #     print ('Files: {0}'.format(filename))
                #os.rename(filename, philename)
                #print ('Original File Name: {0}'.format(filename))
                #dirspot = os.getcwd()
                #print ('Starting Directory: {0}'.format(dirspot))
                #filename_without_ext = os.path.splitext(filename)[0]
                #extension = os.path.splitext(filename)[1]
                #new_file_name = "carthage_applications"
                #new_file_name_with_ext = new_file_name+extension
                #print ('New File Name: {0}'.format(new_file_name_with_ext))
                #print ('New Directory: {0}'.format(archived_destination))
                #os.rename(os.path.join(destination,filename),os.path.join(destination,new_file_name_with_ext))
                #time.sleep(3)
                #shutil.move(new_file_name_with_ext,archived_destination)
                #shutil.move(new_file_name_with_ext,archived_destination)
                # time.sleep(3)
                # os.chdir(settings.COMMONAPP_CSV_ARCHIVED)
                # dirspot = os.getcwd()
                # print ('New Directory: {0}'.format(dirspot))
                
                #archived_file_name = new_file_name+datetimestr+extension
                #os.rename(os.path.join(archived_destination,new_file_name_with_ext),os.path.join(archived_destination,archived_file_name))
                
            # sftp.get(filename, preserve_mtime=True)
            #sftp.close()
    # except Exception, e:
    #     print e
        #SUBJECT = '[Common Application sFTP] failed'
        #BODY = 'Unable to GET download from Common Application server.\n\n{0}'.format(str(e))
        #sendmail(
        #    settings.COMMONAPP_TO_EMAIL,settings.COMMONAPP_FROM_EMAIL,
        #    SUBJECT, BODY
        #)

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())