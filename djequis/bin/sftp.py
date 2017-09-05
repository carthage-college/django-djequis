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
    os.chdir('/data2/www/data/everbridge/')
    filename = 'FacStaffUpload-20170111095440.csv'
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
        'host':settings.EVERBRIDGE_HOST,
        'username':settings.EVERBRIDGE_USER,
        'private_key':settings.EVERBRIDGE_PKEY,
        'cnopts':cnopts
    }
    # transfer the CSV to scripsafe
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        sftp.chdir("replace/")
        #sftp.put(filename, remotepath="replace/", preserve_mtime=True)
        sftp.put(filename, preserve_mtime=True)
        sftp.close()

    print "done"

if __name__ == '__main__':

    sys.exit(main())
