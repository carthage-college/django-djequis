import os
import sys
import ftplib

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

import django
django.setup()

from django.conf import settings


def main():
    # transfer the PDFs to scripsafe

    ftp = ftplib.FTP(
        settings.XTRNL_SRVR, settings.XTRNL_USER, settings.XTRNL_PASS
    )
    ftp.cwd(settings.XTRNL_PATH)
    print ftp.pwd()
    #ftp.retrlines('LIST')
    phile = open('/home/skirk/carthage_personas_draft_20161204020018.xml','rb')
    ftp.storlines("STOR " + 'carthage_personas_draft_20161204020018.xml', phile)
    phile.close()
    ftp.quit()

    print "end"

if __name__ == "__main__":

    sys.exit(main())
