import io
import os
import re
import sys
import pysftp

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.8/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

from django.conf import settings


def main():
    # go to our storage directory on this server
    os.chdir('/data2/www/data/terradotta/')
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
        'host':settings.TERRADOTTA_HOST,
        'username':settings.TERRADOTTA_USER,
        'private_key':settings.TERRADOTTA_PKEY,
        'password':settings.TERRADOTTA_PASS,
        'cnopts':cnopts
    }
    # transfer the CSV to scripsafe
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        sftp.put("sis_hr_user_info.txt", preserve_mtime=True)


    print "files sent to script safe:\n{}".format(philes)

if __name__ == "__main__":

    sys.exit(main())
