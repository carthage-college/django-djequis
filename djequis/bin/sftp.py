import io
import os
import re
import sys
import pysftp

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djequis.settings')

from django.conf import settings


def main():
    # go to our storage directory on this server
    #os.chdir('/data2/www/data/terradotta/')
    #filename = 'sis_hr_user_info.txt'
    #os.chdir('/data2/www/data/everbridge/')
    #filename = 'FacStaffUpload-20170111095440.csv'
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # External connection information for Common Application server
    XTRNL_CONNECTION = {
       'host':settings.COMMONAPP_HOST,
       'username':settings.COMMONAPP_USER,
       'password':settings.COMMONAPP_PASS,
       'cnopts':cnopts
    }
    try:
        with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
            remotepath = sftp.listdir()
            print(remotepath)
            # Loop through remote path directory list
            for filename in remotepath:
                remotefile = filename
                # set local directory for which the common app file will be downloaded to
                local_dir = ('{0}'.format(
                    settings.COMMONAPP_CSV_OUTPUT
                ))
                localpath = local_dir + remotefile
                # GET file from sFTP server and download it to localpath
                sftp.get(remotefile, localpath)
                #############################################################
                # Delete original file %m_%d_%y_%h_%i_%s_Applications(%c).txt
                # from sFTP (Common App) server
                #############################################################
                sftp.remove(filename)
        # closes sftp connection
        sftp.close()
    except Exception, e:
        print('Unable to connect to Common App server.\n\n{0}'.format(str(e)))
        

if __name__ == '__main__':

    sys.exit(main())
